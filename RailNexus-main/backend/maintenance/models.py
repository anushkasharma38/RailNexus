from django.db import models
from railway.models import Asset, RailwaySection


DEPARTMENTS = [
    ("ENGINEERING", "Engineering"),
    ("TRACTION", "Traction"),
    ("S_AND_T", "S&T"),
]


class MaintenanceTask(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        REQUESTED = "REQUESTED", "Block Requested"
        PLANNED = "PLANNED", "Planned"
        COMPLETED = "COMPLETED", "Completed"

    task_id = models.CharField(max_length=20, unique=True)
    title = models.CharField(max_length=160)
    department = models.CharField(max_length=20, choices=DEPARTMENTS)
    section = models.ForeignKey(RailwaySection, on_delete=models.CASCADE, related_name="tasks")
    asset = models.ForeignKey(Asset, on_delete=models.SET_NULL, null=True, related_name="tasks")
    criticality = models.PositiveSmallIntegerField(default=3)
    urgency = models.PositiveSmallIntegerField(default=3)
    safety_risk = models.PositiveSmallIntegerField(default=3)
    asset_impact = models.PositiveSmallIntegerField(default=3)
    estimated_duration = models.PositiveIntegerField(help_text="Minutes")
    preferred_date = models.DateField()
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.PENDING)

    class Meta:
        ordering = ["preferred_date", "task_id"]

    def __str__(self):
        return f"{self.task_id}: {self.title}"


class BlockRequest(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        PLANNED = "PLANNED", "Planned"
        REJECTED = "REJECTED", "Rejected"

    maintenance_task = models.ForeignKey(MaintenanceTask, on_delete=models.CASCADE, related_name="block_requests")
    requested_start = models.DateTimeField()
    requested_end = models.DateTimeField()
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    remarks = models.TextField(blank=True)

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.requested_end <= self.requested_start:
            raise ValidationError("Requested end must be after requested start.")


class Alert(models.Model):
    class Severity(models.TextChoices):
        CRITICAL = "CRITICAL", "Critical"
        HIGH = "HIGH", "High"
        MEDIUM = "MEDIUM", "Medium"
        LOW = "LOW", "Low"

    title = models.CharField(max_length=120)
    message = models.TextField()
    severity = models.CharField(max_length=10, choices=Severity.choices)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]


class ExecutionRecord(models.Model):
    class Status(models.TextChoices):
        COMPLETED = "COMPLETED", "Completed"
        DELAYED = "DELAYED", "Delayed"
        CANCELLED = "CANCELLED", "Cancelled"
        PARTIAL = "PARTIAL", "Partially Completed"

    block_plan = models.OneToOneField("planning.BlockPlan", on_delete=models.CASCADE, related_name="execution")
    actual_start = models.DateTimeField()
    actual_end = models.DateTimeField()
    status = models.CharField(max_length=12, choices=Status.choices)
    remarks = models.TextField(blank=True)

    @property
    def variance_minutes(self):
        return int((self.actual_end - self.block_plan.end_time).total_seconds() / 60)
