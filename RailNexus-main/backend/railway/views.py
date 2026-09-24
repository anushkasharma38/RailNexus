from rest_framework.viewsets import ModelViewSet
from accounts.permissions import RoleWritePermission
from .models import Asset, GoodsTrainForecast, RailwaySection, Train, TrainSchedule
from .serializers import (
    AssetSerializer,
    GoodsTrainForecastSerializer,
    RailwaySectionSerializer,
    TrainScheduleSerializer,
    TrainSerializer,
)


class RailwaySectionViewSet(ModelViewSet):
    permission_classes = [RoleWritePermission]
    queryset = RailwaySection.objects.order_by("id")
    serializer_class = RailwaySectionSerializer


class AssetViewSet(ModelViewSet):
    permission_classes = [RoleWritePermission]
    queryset = Asset.objects.select_related("section").order_by("id")
    serializer_class = AssetSerializer


class TrainViewSet(ModelViewSet):
    permission_classes = [RoleWritePermission]
    queryset = Train.objects.order_by("id")
    serializer_class = TrainSerializer


class TrainScheduleViewSet(ModelViewSet):
    permission_classes = [RoleWritePermission]
    queryset = TrainSchedule.objects.select_related("train", "section").order_by("arrival_time")
    serializer_class = TrainScheduleSerializer


class GoodsTrainForecastViewSet(ModelViewSet):
    permission_classes = [RoleWritePermission]
    queryset = GoodsTrainForecast.objects.select_related("section").order_by("date", "section")
    serializer_class = GoodsTrainForecastSerializer
