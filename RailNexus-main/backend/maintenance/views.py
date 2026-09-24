from rest_framework.viewsets import ModelViewSet
from accounts.permissions import RoleWritePermission
from .models import Alert, BlockRequest, ExecutionRecord, MaintenanceTask
from .serializers import AlertSerializer, BlockRequestSerializer, ExecutionRecordSerializer, MaintenanceTaskSerializer


class MaintenanceTaskViewSet(ModelViewSet):
    permission_classes = [RoleWritePermission]
    queryset = MaintenanceTask.objects.select_related("section", "asset").all()
    serializer_class = MaintenanceTaskSerializer


class BlockRequestViewSet(ModelViewSet):
    permission_classes = [RoleWritePermission]
    queryset = BlockRequest.objects.select_related("maintenance_task").order_by("-requested_start")
    serializer_class = BlockRequestSerializer


class ExecutionRecordViewSet(ModelViewSet):
    permission_classes = [RoleWritePermission]
    queryset = ExecutionRecord.objects.select_related("block_plan").order_by("-actual_start")
    serializer_class = ExecutionRecordSerializer


class AlertViewSet(ModelViewSet):
    permission_classes = [RoleWritePermission]
    queryset = Alert.objects.all()
    serializer_class = AlertSerializer
