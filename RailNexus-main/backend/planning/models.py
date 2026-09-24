from django.db import models
from maintenance.models import BlockRequest, MaintenanceTask
from railway.models import RailwaySection


class BlockPlan(models.Model):
    class Status(models.TextChoices):
        GENERATED = "GENERATED", "Generated"
        PENDING = "PENDING_APPROVAL", "Pending Approval"
        APPROVED = "APPROVED", "Approved"
        MODIFIED = "MODIFIED", "Modified"
        REJECTED = "REJECTED", "Rejected"
        COMPLETED = "COMPLETED", "Completed"

    section = models.ForeignKey(RailwaySection, on_delete=models.CASCADE, related_name="block_plans")
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    priority_score = models.DecimalField(max_digits=5, decimal_places=2)
    utilization = models.DecimalField(max_digits=5, decimal_places=2, default=100)
    reason = models.TextField()
    tasks = models.ManyToManyField(MaintenanceTask, through="BlockPlanTask", related_name="block_plans")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["start_time"]
        indexes = [models.Index(fields=["section", "start_time"])]


class BlockPlanTask(models.Model):
    block_plan = models.ForeignKey(BlockPlan, on_delete=models.CASCADE)
    maintenance_task = models.ForeignKey(MaintenanceTask, on_delete=models.CASCADE)

    class Meta:
        unique_together = ("block_plan", "maintenance_task")


class Conflict(models.Model):
    class Severity(models.TextChoices):
        CRITICAL = "CRITICAL", "Critical"
        HIGH = "HIGH", "High"
        MEDIUM = "MEDIUM", "Medium"
        LOW = "LOW", "Low"

    block_plan = models.ForeignKey(BlockPlan, null=True, blank=True, on_delete=models.CASCADE, related_name="conflicts")
    block_request = models.ForeignKey(BlockRequest, null=True, blank=True, on_delete=models.CASCADE, related_name="conflicts")
    conflict_type = models.CharField(max_length=40)
    description = models.TextField()
    severity = models.CharField(max_length=10, choices=Severity.choices)
    resolved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
