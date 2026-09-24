from django.db import transaction
from rest_framework import serializers
from planning.services import PriorityEngine
from .models import Alert, BlockRequest, ExecutionRecord, MaintenanceTask


class MaintenanceTaskSerializer(serializers.ModelSerializer):
    section_name = serializers.CharField(source="section.name", read_only=True)
    asset_name = serializers.CharField(source="asset.name", read_only=True)
    priority = serializers.SerializerMethodField()

    class Meta:
        model = MaintenanceTask
        fields = "__all__"

    def validate(self, attrs):
        for field in ("criticality", "urgency", "safety_risk", "asset_impact"):
            value = attrs.get(field, getattr(self.instance, field, None))
            if value is not None and not 1 <= value <= 5:
                raise serializers.ValidationError({field: "Must be between 1 and 5."})
        duration = attrs.get("estimated_duration", getattr(self.instance, "estimated_duration", None))
        if duration is not None and duration < 15:
            raise serializers.ValidationError({"estimated_duration": "Must be at least 15 minutes."})
        section = attrs.get("section", getattr(self.instance, "section", None))
        asset = attrs.get("asset", getattr(self.instance, "asset", None))
        if section and asset and asset.section_id != section.id:
            raise serializers.ValidationError({"asset": "Asset must belong to the selected section."})
        return attrs

    def get_priority(self, obj):
        return PriorityEngine().calculate_score(obj)


class BlockRequestSerializer(serializers.ModelSerializer):
    task_title = serializers.CharField(source="maintenance_task.title", read_only=True)

    class Meta:
        model = BlockRequest
        fields = "__all__"

    def validate(self, attrs):
        start = attrs.get("requested_start", getattr(self.instance, "requested_start", None))
        end = attrs.get("requested_end", getattr(self.instance, "requested_end", None))
        if start and end and end <= start:
            raise serializers.ValidationError("Requested end must be after requested start.")
        return attrs

    def create(self, validated_data):
        instance = super().create(validated_data)
        task = instance.maintenance_task
        task.status = "REQUESTED"
        task.save(update_fields=["status"])
        return instance


class ExecutionRecordSerializer(serializers.ModelSerializer):
    variance_minutes = serializers.IntegerField(read_only=True)
    planned_start = serializers.DateTimeField(source="block_plan.start_time", read_only=True)
    planned_end = serializers.DateTimeField(source="block_plan.end_time", read_only=True)

    class Meta:
        model = ExecutionRecord
        fields = "__all__"

    def validate(self, attrs):
        start = attrs.get("actual_start", getattr(self.instance, "actual_start", None))
        end = attrs.get("actual_end", getattr(self.instance, "actual_end", None))
        if start and end and end <= start:
            raise serializers.ValidationError("Actual end must be after actual start.")
        return attrs

    @staticmethod
    def _apply_status(record, previous_status=None):
        if record.status == "COMPLETED":
            record.block_plan.status = "COMPLETED"
            record.block_plan.save(update_fields=["status"])
            record.block_plan.tasks.update(status="COMPLETED")
        elif record.status in {"DELAYED", "CANCELLED"} and record.status != previous_status:
            Alert.objects.create(
                title=f"Execution {record.get_status_display()}",
                message=f"Plan #{record.block_plan_id} execution requires attention.",
                severity="HIGH",
            )

    @transaction.atomic
    def create(self, validated_data):
        record = super().create(validated_data)
        self._apply_status(record)
        return record

    @transaction.atomic
    def update(self, instance, validated_data):
        previous_status = instance.status
        record = super().update(instance, validated_data)
        self._apply_status(record, previous_status)
        return record


class AlertSerializer(serializers.ModelSerializer):
    class Meta:
        model = Alert
        fields = "__all__"
