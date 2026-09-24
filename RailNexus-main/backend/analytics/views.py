from datetime import date, timedelta

from django.db.models import Avg, Count
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from maintenance.models import Alert, ExecutionRecord, MaintenanceTask
from maintenance.serializers import AlertSerializer, MaintenanceTaskSerializer
from planning.models import BlockPlan, Conflict
from planning.serializers import BlockPlanSerializer
from planning.services import BottleneckDetector, PriorityEngine
from railway.models import Asset, RailwaySection


def availability_for(queryset):
    total = queryset.count()
    available = queryset.exclude(health_status="UNAVAILABLE").count()
    return round(available / total * 100, 1) if total else 100


def scoped_data(user):
    department = user.role if user.role in {"ENGINEERING", "TRACTION", "S_AND_T"} else None
    tasks = MaintenanceTask.objects.select_related("section", "asset")
    plans = BlockPlan.objects.select_related("section").prefetch_related("tasks")
    assets = Asset.objects.select_related("section")
    conflicts = Conflict.objects.select_related("block_plan")
    executions = ExecutionRecord.objects.select_related("block_plan")
    if department:
        tasks = tasks.filter(department=department)
        plans = plans.filter(tasks__department=department).distinct()
        assets = assets.filter(tasks__department=department).distinct()
        conflicts = conflicts.filter(block_plan__tasks__department=department).distinct()
        executions = executions.filter(block_plan__tasks__department=department).distinct()
    return {
        "department": department,
        "tasks": tasks,
        "plans": plans,
        "assets": assets,
        "conflicts": conflicts,
        "executions": executions,
    }


def report_payload(user):
    scoped = scoped_data(user)
    tasks = scoped["tasks"]
    plans = scoped["plans"]
    assets = scoped["assets"]
    conflicts = scoped["conflicts"]
    executions = scoped["executions"]
    execution_rows = list(executions)
    total_executions = len(execution_rows)
    sections = RailwaySection.objects.filter(assets__in=assets).distinct()
    if not scoped["department"]:
        sections = RailwaySection.objects.all()
    bottleneck_sections = sections
    return {
        "source_label": "SIMULATED RAILWAY DATA · PostgreSQL-backed prototype reports",
        "role_scope": scoped["department"] or "SYSTEM_WIDE",
        "block_utilization": {
            "total_blocks": plans.count(),
            "approved_blocks": plans.filter(status="APPROVED").count(),
            "completed_blocks": plans.filter(status="COMPLETED").count(),
            "utilization_percentage": round(plans.aggregate(value=Avg("utilization"))["value"] or 0, 1),
        },
        "maintenance": {
            "total_tasks": tasks.count(),
            "completed": tasks.filter(status="COMPLETED").count(),
            "pending": tasks.exclude(status="COMPLETED").count(),
            "overdue": tasks.exclude(status="COMPLETED").filter(preferred_date__lt=timezone.localdate()).count(),
            "by_department": list(tasks.values("department").annotate(count=Count("id")).order_by("department")),
        },
        "asset_availability": {
            "overall_availability": availability_for(assets),
            "by_section": [
                {
                    "section": section.name,
                    "availability": availability_for(assets.filter(section=section)),
                }
                for section in sections
            ],
        },
        "conflicts": {
            "total_conflicts": conflicts.count(),
            "critical": conflicts.filter(severity="CRITICAL").count(),
            "high": conflicts.filter(severity="HIGH").count(),
            "medium": conflicts.filter(severity="MEDIUM").count(),
            "resolved": conflicts.filter(resolved=True).count(),
            "unresolved": conflicts.filter(resolved=False).count(),
        },
        "planned_vs_actual": {
            "average_schedule_variance": round(
                sum(record.variance_minutes for record in execution_rows) / total_executions, 1
            ) if total_executions else 0,
            "completed_on_time": sum(
                record.status == "COMPLETED" and record.variance_minutes <= 0
                for record in execution_rows
            ),
            "delayed": sum(
                record.status == "DELAYED"
                or (record.status == "COMPLETED" and record.variance_minutes > 0)
                for record in execution_rows
            ),
            "cancelled": sum(record.status == "CANCELLED" for record in execution_rows),
        },
        "bottlenecks": BottleneckDetector().detect(
            timezone.localdate(),
            timezone.localdate() + timedelta(days=6),
            bottleneck_sections,
        )[:12],
    }


class DashboardView(APIView):
    def get(self, request):
        scoped = scoped_data(request.user)
        plans = scoped["plans"]
        tasks = scoped["tasks"]
        assets = scoped["assets"]
        conflicts = scoped["conflicts"]
        critical_tasks = sorted(
            tasks.exclude(status="COMPLETED"),
            key=lambda task: PriorityEngine().calculate_score(task)["score"],
            reverse=True,
        )[:6]
        sections = RailwaySection.objects.filter(tasks__in=tasks).distinct()
        if not scoped["department"]:
            sections = RailwaySection.objects.all()
        return Response({
            "source_label": "Simulated Railway Data",
            "role_scope": scoped["department"] or "SYSTEM_WIDE",
            "stats": {
                "active_blocks": plans.filter(status__in=["PENDING_APPROVAL", "APPROVED", "MODIFIED"]).count(),
                "pending_tasks": tasks.exclude(status="COMPLETED").count(),
                "conflicts": conflicts.filter(resolved=False).count(),
                "asset_availability": availability_for(assets),
                "approval_queue": plans.filter(status="PENDING_APPROVAL").count(),
            },
            "plans": BlockPlanSerializer(plans[:12], many=True).data,
            "alerts": AlertSerializer(Alert.objects.all()[:6], many=True).data,
            "critical_tasks": MaintenanceTaskSerializer(critical_tasks, many=True).data,
            "bottlenecks": BottleneckDetector().detect(
                timezone.localdate(),
                timezone.localdate() + timedelta(days=6),
                sections,
            )[:5],
        })


class AnalyticsView(APIView):
    def get(self, request):
        scoped = scoped_data(request.user)
        section_rows = []
        sections = RailwaySection.objects.filter(assets__in=scoped["assets"]).distinct()
        for section in sections:
            section_rows.append({
                "section": section.name,
                "availability": availability_for(scoped["assets"].filter(section=section)),
            })
        executions = scoped["executions"]
        completed = executions.filter(status="COMPLETED").count()
        total = executions.count()
        return Response({
            "source_label": "Prototype-generated metrics from Simulated Railway Data",
            "role_scope": scoped["department"] or "SYSTEM_WIDE",
            "asset_availability": availability_for(scoped["assets"]),
            "section_availability": section_rows,
            "block_utilization": round(scoped["plans"].aggregate(value=Avg("utilization"))["value"] or 0, 1),
            "maintenance_completion": round(completed / total * 100, 1) if total else 0,
            "conflict_count": scoped["conflicts"].filter(resolved=False).count(),
            "department_workload": list(scoped["tasks"].values("department").annotate(count=Count("id"))),
            "execution_status": list(executions.values("status").annotate(count=Count("id"))),
            "average_schedule_variance": round(
                sum(record.variance_minutes for record in executions) / total, 1
            ) if total else 0,
        })


class BottleneckView(APIView):
    def get(self, request):
        scoped = scoped_data(request.user)
        sections = RailwaySection.objects.filter(tasks__in=scoped["tasks"]).distinct()
        if not scoped["department"]:
            sections = RailwaySection.objects.all()
        return Response(BottleneckDetector().detect(
            timezone.localdate(),
            timezone.localdate() + timedelta(days=6),
            sections,
        ))


class PlanningCalendarView(APIView):
    def get(self, request):
        try:
            start_date = date.fromisoformat(request.query_params.get("start", ""))
            end_date = date.fromisoformat(request.query_params.get("end", ""))
        except ValueError:
            return Response(
                {"detail": "Valid start and end dates are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if end_date < start_date or end_date - start_date > timedelta(days=62):
            return Response(
                {"detail": "Calendar range must be between 1 and 63 days."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        plans = scoped_data(request.user)["plans"].filter(
            start_time__date__gte=start_date,
            start_time__date__lte=end_date,
        )
        return Response({
            "source_label": "SIMULATED RAILWAY DATA",
            "start": start_date.isoformat(),
            "end": end_date.isoformat(),
            "plans": BlockPlanSerializer(plans, many=True).data,
        })


class ReportsView(APIView):
    def get(self, request):
        return Response(report_payload(request.user))
