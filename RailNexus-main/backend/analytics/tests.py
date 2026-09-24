from datetime import datetime, time, timedelta

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from accounts.models import User
from maintenance.models import ExecutionRecord, MaintenanceTask
from planning.models import BlockPlan, BlockPlanTask, Conflict
from railway.models import Asset, RailwaySection


def aware(day, hour):
    return timezone.make_aware(datetime.combine(day, time(hour)))


class CompletionApiTests(TestCase):
    def setUp(self):
        self.day = timezone.localdate() + timedelta(days=1)
        self.engineer = User.objects.create_user("engineer-report", password="pass", role="ENGINEERING")
        self.control = User.objects.create_user("control-report", password="pass", role="CONTROL_OFFICE")
        self.client = APIClient()
        self.section_a = RailwaySection.objects.create(
            name="Engineering Section", code="ENG-SEC", start_station="A",
            end_station="B", length=20,
        )
        self.section_b = RailwaySection.objects.create(
            name="Traction Section", code="TRC-SEC", start_station="B",
            end_station="C", length=25,
        )
        self.asset_a = Asset.objects.create(
            name="Engineering Asset", asset_type="Track", section=self.section_a,
            health_status="DUE", criticality=5,
        )
        self.asset_b = Asset.objects.create(
            name="Traction Asset", asset_type="OHE", section=self.section_b,
            health_status="GOOD", criticality=3,
        )
        self.task_a = MaintenanceTask.objects.create(
            task_id="ENG-R1", title="Engineering work", department="ENGINEERING",
            section=self.section_a, asset=self.asset_a, criticality=5, urgency=4,
            safety_risk=4, asset_impact=5, estimated_duration=60,
            preferred_date=self.day,
        )
        self.task_b = MaintenanceTask.objects.create(
            task_id="TRC-R1", title="Traction work", department="TRACTION",
            section=self.section_b, asset=self.asset_b, criticality=3, urgency=3,
            safety_risk=3, asset_impact=3, estimated_duration=60,
            preferred_date=self.day,
        )
        self.plan_a = BlockPlan.objects.create(
            section=self.section_a, start_time=aware(self.day, 10),
            end_time=aware(self.day, 11), status="COMPLETED",
            priority_score=85, utilization=80, reason="Engineering plan",
        )
        self.plan_b = BlockPlan.objects.create(
            section=self.section_b, start_time=aware(self.day, 12),
            end_time=aware(self.day, 13), status="APPROVED",
            priority_score=60, utilization=60, reason="Traction plan",
        )
        BlockPlanTask.objects.create(block_plan=self.plan_a, maintenance_task=self.task_a)
        BlockPlanTask.objects.create(block_plan=self.plan_b, maintenance_task=self.task_b)
        Conflict.objects.create(
            block_plan=self.plan_a, conflict_type="TRAIN_VS_BLOCK",
            description="Test conflict", severity="HIGH",
        )
        self.execution = ExecutionRecord.objects.create(
            block_plan=self.plan_a, actual_start=aware(self.day, 10),
            actual_end=aware(self.day, 11) + timedelta(minutes=15),
            status="DELAYED",
        )

    def test_role_aware_dashboard_filters_department_data(self):
        self.client.force_authenticate(self.engineer)
        response = self.client.get("/api/dashboard/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["role_scope"], "ENGINEERING")
        self.assertEqual(len(response.data["plans"]), 1)
        self.assertTrue(all(
            task["department"] == "ENGINEERING"
            for task in response.data["critical_tasks"]
        ))
        self.assertEqual(response.data["stats"]["asset_availability"], 100)

    def test_reports_calculate_from_scoped_database_records(self):
        self.client.force_authenticate(self.control)
        response = self.client.get("/api/reports/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["block_utilization"]["total_blocks"], 2)
        self.assertEqual(response.data["block_utilization"]["completed_blocks"], 1)
        self.assertEqual(response.data["maintenance"]["total_tasks"], 2)
        self.assertEqual(response.data["conflicts"]["unresolved"], 1)
        self.assertEqual(response.data["planned_vs_actual"]["average_schedule_variance"], 15)
        self.assertEqual(response.data["planned_vs_actual"]["delayed"], 1)

    def test_calendar_range_supports_week_and_month_data(self):
        self.client.force_authenticate(self.engineer)
        start = self.day.isoformat()
        end = (self.day + timedelta(days=30)).isoformat()
        response = self.client.get(f"/api/calendar/?start={start}&end={end}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["start"], self.day.isoformat())
        self.assertEqual(len(response.data["plans"]), 1)
        self.assertEqual(response.data["plans"][0]["section_name"], "Engineering Section")

    def test_execution_update_applies_completion_feedback(self):
        self.client.force_authenticate(self.control)
        response = self.client.patch(
            f"/api/execution/{self.execution.id}/",
            {"status": "COMPLETED"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.plan_a.refresh_from_db()
        self.task_a.refresh_from_db()
        self.assertEqual(self.plan_a.status, "COMPLETED")
        self.assertEqual(self.task_a.status, "COMPLETED")
