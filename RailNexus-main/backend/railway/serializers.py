from rest_framework import serializers
from .models import Asset, GoodsTrainForecast, RailwaySection, Train, TrainSchedule


class RailwaySectionSerializer(serializers.ModelSerializer):
    asset_count = serializers.IntegerField(source="assets.count", read_only=True)

    class Meta:
        model = RailwaySection
        fields = "__all__"


class AssetSerializer(serializers.ModelSerializer):
    section_name = serializers.CharField(source="section.name", read_only=True)

    class Meta:
        model = Asset
        fields = "__all__"


class TrainSerializer(serializers.ModelSerializer):
    class Meta:
        model = Train
        fields = "__all__"


class TrainScheduleSerializer(serializers.ModelSerializer):
    train_number = serializers.CharField(source="train.train_number", read_only=True)
    train_name = serializers.CharField(source="train.name", read_only=True)
    section_name = serializers.CharField(source="section.name", read_only=True)

    class Meta:
        model = TrainSchedule
        fields = "__all__"

    def validate(self, attrs):
        start = attrs.get("arrival_time", getattr(self.instance, "arrival_time", None))
        end = attrs.get("departure_time", getattr(self.instance, "departure_time", None))
        if start and end and end <= start:
            raise serializers.ValidationError("Departure time must be after arrival time.")
        return attrs


class GoodsTrainForecastSerializer(serializers.ModelSerializer):
    section_name = serializers.CharField(source="section.name", read_only=True)
    source_label = serializers.CharField(default="SIMULATED RAILWAY DATA", read_only=True)

    class Meta:
        model = GoodsTrainForecast
        fields = "__all__"
