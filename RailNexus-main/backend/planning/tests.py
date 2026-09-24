from datetime import datetime, time, timedelta

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from accounts.models import User
from maintenance.models import BlockRequest, ExecutionRecord, MaintenanceTask
from railway.models import Asset, GoodsTrainForecast, RailwaySection, Train, TrainSchedule
from railway.providers import (
    GoodsTrainForecastProvider,
    SMMSDataProvider,
    TDMSDataProvider,
    TMSDataProvider,
    TrainTimetableProvider,
)
from .models import BlockPlan
from .services import (
    BlockOptimizer,
    BottleneckDetector,
    ConflictDetector,
    PriorityEngine,
    ReplanningService,
    ScenarioSimulator,
)


def aware(day, hour, minute=0):
    return timezone.make_aware(datetime.combine(day, time(hour, minute)))


class PlanningEngineTests(TestCase):
    def setUp(self):
        self.day = timezone.localdate() + timedelta(days=1)
        self.section = RailwaySection.objects.create(
            name="Test Corridor", code="TST-ONE", start_station="Alpha",
            end_station="Beta", length=10, status="AVAILABLE",
        )
        self.asset = Asset.objects.create(
            name="Test Point", asset_type="Point Machine", section=self.section,
            health_status="DUE", criticality=5,
        )

    def task(self, task_id, department="ENGINEERING", **overrides):
        values = {
            "title": "Safety maintenance", "section": self.section, "asset": self.asset,
            "criticality": 5, "urgency": 5, "safety_risk": 5, "asset_impact": 5,
            "estimated_duration": 60, "preferred_date": self.day,
        }
        values.update(overrides)
        return MaintenanceTask.objects.create(task_id=task_id, department=department, **values)

    def test_priority_score_is_explainable(self):
        task = self.task("T-1")
        result = PriorityEngine().calculate_score(task)
        self.assertEqual(result["score"], 92)
        self.assertEqual(result["level"], "CRITICAL")
        self.assertIn("High safety risk", result["reasons"])
        self.assertEqual(result, PriorityEngine().calculate_score(task))
        self.assertGreaterEqual(result["score"], 0)
        self.assertLessEqual(result["score"], 100)

    def test_train_block_conflict(self):
        train = Train.objects.create(train_number="T100", name="Test Train", train_type="Demo")
        TrainSchedule.objects.create(
            train=train, section=self.section, arrival_time=aware(self.day, 10),
            departure_time=aware(self.day, 10, 30), date=self.day,
        )
        conflicts = ConflictDetector().detect(self.section, aware(self.day, 9, 45), aware(self.day, 10, 15))
        self.assertEqual(conflicts[0]["type"], "TRAIN_VS_BLOCK")

    def test_optimizer_groups_departments(self):
        first = self.task("T-2", "ENGINEERING")
        second = self.task("T-3", "S_AND_T", estimated_duration=90)
        plans = BlockOptimizer().generate([first.id, second.id])
        self.assertEqual(len(plans), 1)
        self.assertEqual(plans[0].tasks.count(), 2)
        self.assertIn("2 maintenance activities coordinated", plans[0].reason)

    def test_optimizer_moves_after_train(self):
        task = self.task("T-4")
        train = Train.objects.create(train_number="T200", name="Window Train", train_type="Demo")
        TrainSchedule.objects.create(
            train=train, section=self.section, arrival_time=aware(self.day, 9),
            departure_time=aware(self.day, 10), date=self.day,
        )
        plan = BlockOptimizer().generate([task.id])[0]
        self.assertGreaterEqual(plan.start_time, aware(self.day, 10))

    def test_requested_1100_to_1300_conflicts_with_noon_train_and_moves(self):
        task = self.task("T-4A", estimated_duration=120)
        BlockRequest.objects.create(
            maintenance_task=task,
            requested_start=aware(self.day, 11),
            requested_end=aware(self.day, 13),
        )
        train = Train.objects.create(train_number="T201", name="Noon Train", train_type="Demo")
        TrainSchedule.objects.create(
            train=train, section=self.section, arrival_time=aware(self.day, 12),
            departure_time=aware(self.day, 12, 30), date=self.day,
        )
        self.assertTrue(ConflictDetector().detect(
            self.section, aware(self.day, 11), aware(self.day, 13)
        ))
        plan = BlockOptimizer().generate([task.id])[0]
        self.assertGreaterEqual(plan.start_time, aware(self.day, 12, 30))
        self.assertFalse(ConflictDetector().detect(
            self.section, plan.start_time, plan.end_time, plan.id
        ))

    def test_overdue_task_uses_requested_window_date(self):
        task = self.task(
            "T-4B",
            preferred_date=timezone.localdate() - timedelta(days=1),
        )
        BlockRequest.objects.create(
            maintenance_task=task,
            requested_start=aware(self.day, 13),
            requested_end=aware(self.day, 14),
        )
        plan = BlockOptimizer().generate([task.id])[0]
        self.assertEqual(plan.start_time, aware(self.day, 13))

    def test_what_if_does_not_mutate_plan(self):
        plan = BlockOptimizer().generate([self.task("T-5").id])[0]
        original = plan.start_time
        result = ScenarioSimulator().simulate(plan, start_shift=30)
        plan.refresh_from_db()
        self.assertEqual(plan.start_time, original)
        self.assertNotEqual(result["before"]["start"], result["after"]["start"])

    def test_what_if_reports_invalid_duration_and_unavailable_section(self):
        plan = BlockOptimizer().generate([self.task("T-5A").id])[0]
        invalid = ScenarioSimulator().simulate(plan, duration_change=-61)
        self.assertEqual(invalid["conflict_details"][0]["type"], "INVALID_TIME")
        self.section.status = "RESTRICTED"
        self.section.save(update_fields=["status"])
        plan.section.refresh_from_db()
        unavailable = ScenarioSimulator().simulate(plan)
        self.assertEqual(unavailable["conflict_details"][0]["type"], "SECTION_AVAILABILITY")

    def test_replanning_moves_plan_after_delayed_train(self):
        plan = BlockPlan.objects.create(
            section=self.section, start_time=aware(self.day, 14),
            end_time=aware(self.day, 16), priority_score=80, utilization=75,
            reason="Original plan.",
        )
        train = Train.objects.create(train_number="T202", name="Delayed Train", train_type="Demo")
        TrainSchedule.objects.create(
            train=train, section=self.section, arrival_time=aware(self.day, 13, 30),
            departure_time=aware(self.day, 14), date=self.day,
        )
        result = ReplanningService().replan(plan, 30)
        self.assertEqual(result["before"]["start"], aware(self.day, 14))
        self.assertEqual(result["after"]["start"], aware(self.day, 14, 30))
        self.assertFalse(ConflictDetector().detect(
            self.section, plan.start_time, plan.end_time, plan.id
        ))

    def test_asset_aware_window_explains_critical_downtime_choice(self):
        plan = BlockOptimizer().generate([self.task("T-6").id])[0]
        self.assertIn("minimize critical asset downtime", plan.reason)

    def test_high_goods_forecast_adds_train_traffic_buffer(self):
        task = self.task("T-7")
        BlockRequest.objects.create(
            maintenance_task=task,
            requested_start=aware(self.day, 9),
            requested_end=aware(self.day, 10),
        )
        train = Train.objects.create(train_number="G700", name="Forecast Goods", train_type="Goods")
        TrainSchedule.objects.create(
            train=train, section=self.section, arrival_time=aware(self.day, 10),
            departure_time=aware(self.day, 10, 30), date=self.day,
        )
        GoodsTrainForecast.objects.create(
            date=self.day, section=self.section,
            expected_train_count=14, forecast_level="HIGH",
        )
        plan = BlockOptimizer().generate([task.id])[0]
        self.assertGreaterEqual(plan.start_time, aware(self.day, 11))
        self.assertIn("HIGH goods train forecast", plan.reason)

    def test_bottleneck_detector_returns_explicit_explanation(self):
        self.section.status = "CLOSED"
        self.section.save(update_fields=["status"])
        self.task("T-8")
        result = BottleneckDetector().detect(self.day, self.day, [self.section])[0]
        self.assertEqual(result["severity"], "HIGH")
        self.assertEqual(result["available_windows"], 0)
        self.assertEqual(result["maintenance_demand"], 1)
        self.assertEqual(len(result["reason"]), 3)

    def test_source_specific_adapters_use_simulated_database(self):
        task = self.task("T-9", department="S_AND_T")
        GoodsTrainForecast.objects.create(
            date=self.day, section=self.section,
            expected_train_count=8, forecast_level="MEDIUM",
        )
        self.assertEqual(TMSDataProvider().get_maintenance_data().count(), 1)
        self.assertEqual(SMMSDataProvider().get_signalling_data().get(), task)
        self.assertEqual(TDMSDataProvider().get_traction_asset_data().count(), 0)
        self.assertEqual(TrainTimetableProvider().source_label, "SIMULATED RAILWAY DATA")
        self.assertEqual(GoodsTrainForecastProvider().get_forecast(self.section, self.day).count(), 1)


class ApiTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("control", password="test-pass", role="CONTROL_OFFICE")
        self.client = APIClient()
        self.section = RailwaySection.objects.create(
            name="API Corridor", code="API-ONE", start_station="A", end_station="B", length=20
        )

    def test_authentication_and_endpoint_basics(self):
        self.assertEqual(self.client.get("/api/sections/").status_code, 401)
        response = self.client.post("/api/auth/login/", {"username": "control", "password": "test-pass"}, format="json")
        self.assertEqual(response.status_code, 200)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {response.data['token']}")
        self.assertEqual(self.client.get("/api/sections/").status_code, 200)
        self.assertEqual(self.client.get("/api/dashboard/").status_code, 200)

    def test_only_control_role_can_review(self):
        plan = BlockPlan.objects.create(
            section=self.section, start_time=timezone.now(), end_time=timezone.now() + timedelta(hours=1),
            priority_score=70, utilization=80, reason="Test",
        )
        engineer = User.objects.create_user("engineer", password="pass", role="ENGINEERING")
        self.client.force_authenticate(engineer)
        response = self.client.post(f"/api/block-plans/{plan.id}/review/", {"decision": "approve"}, format="json")
        self.assertEqual(response.status_code, 403)

    def test_department_role_cannot_run_or_replan(self):
        engineer = User.objects.create_user("engineer-actions", password="pass", role="ENGINEERING")
        self.client.force_authenticate(engineer)
        self.assertEqual(self.client.post("/api/planning/run/", {}, format="json").status_code, 403)
        self.assertEqual(
            self.client.post("/api/planning/replan/", {"plan_id": 1}, format="json").status_code,
            403,
        )

    def test_planning_actions_validate_identifiers_and_numbers(self):
        self.client.force_authenticate(self.user)
        self.assertEqual(
            self.client.post("/api/planning/simulate/", {}, format="json").status_code,
            400,
        )
        plan = BlockPlan.objects.create(
            section=self.section, start_time=timezone.now(),
            end_time=timezone.now() + timedelta(hours=1),
            priority_score=70, utilization=80, reason="Validation test",
        )
        self.assertEqual(
            self.client.post(
                "/api/planning/simulate/",
                {"plan_id": plan.id, "train_delay": "bad"},
                format="json",
            ).status_code,
            400,
        )
        self.assertEqual(
            self.client.post(
                "/api/planning/simulate/",
                {"plan_id": 99999, "train_delay": "bad"},
                format="json",
            ).status_code,
            404,
        )

    def test_analytics_uses_execution_records(self):
        plan = BlockPlan.objects.create(
            section=self.section, start_time=timezone.now(),
            end_time=timezone.now() + timedelta(hours=1),
            priority_score=70, utilization=80, reason="Analytics test",
        )
        ExecutionRecord.objects.create(
            block_plan=plan, actual_start=plan.start_time,
            actual_end=plan.end_time + timedelta(minutes=15), status="COMPLETED",
        )
        self.client.force_authenticate(self.user)
        response = self.client.get("/api/analytics/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["average_schedule_variance"], 15)
        self.assertEqual(response.data["maintenance_completion"], 100)
