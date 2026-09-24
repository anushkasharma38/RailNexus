from rest_framework import serializers
from maintenance.serializers import MaintenanceTaskSerializer
from .models import BlockPlan, Conflict


class ConflictSerializer(serializers.ModelSerializer):
    class Meta:
        model = Conflict
        fields = "__all__"


class BlockPlanSerializer(serializers.ModelSerializer):
    section_name = serializers.CharField(source="section.name", read_only=True)
    tasks_detail = MaintenanceTaskSerializer(source="tasks", many=True, read_only=True)
    conflicts_detail = ConflictSerializer(source="conflicts", many=True, read_only=True)
    departments = serializers.SerializerMethodField()

    class Meta:
        model = BlockPlan
        fields = "__all__"

    def validate(self, attrs):
        start = attrs.get("start_time", getattr(self.instance, "start_time", None))
        end = attrs.get("end_time", getattr(self.instance, "end_time", None))
        if start and end and end <= start:
            raise serializers.ValidationError("End time must be after start time.")
        return attrs

    def get_departments(self, obj):
        return sorted({task.department for task in obj.tasks.all()})
