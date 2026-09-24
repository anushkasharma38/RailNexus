from datetime import datetime, time, timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from accounts.models import User
from maintenance.models import Alert, BlockRequest, ExecutionRecord, MaintenanceTask
from planning.models import BlockPlan, BlockPlanTask, Conflict
from railway.models import Asset, GoodsTrainForecast, RailwaySection, Train, TrainSchedule


def at(day, hour, minute=0):
    return timezone.make_aware(datetime.combine(day, time(hour, minute)))


def seed_goods_forecasts(sections, today):
    levels = [
        ("DMD-NGP", [(8, "MEDIUM"), (13, "HIGH"), (6, "LOW")]),
        ("NGP-KSV", [(5, "LOW"), (9, "MEDIUM"), (12, "HIGH")]),
        ("KSV-RJN", [(10, "MEDIUM"), (14, "HIGH"), (7, "LOW")]),
    ]
    by_code = {section.code: section for section in sections}
    for code, pattern in levels:
        if code not in by_code:
            continue
        for offset in range(7):
            count, level = pattern[offset % len(pattern)]
            GoodsTrainForecast.objects.update_or_create(
                section=by_code[code],
                date=today + timedelta(days=offset),
                defaults={"expected_train_count": count, "forecast_level": level},
            )


class Command(BaseCommand):
    help = "Create an idempotent RailNexus simulated demonstration dataset."

    def handle(self, *args, **options):
        password = "RailNexus@2026"
        users = [
            ("admin", "ADMIN", "Administration"),
            ("engineering", "ENGINEERING", "Engineering"),
            ("traction", "TRACTION", "Traction"),
            ("snt", "S_AND_T", "Signal & Telecom"),
            ("control", "CONTROL_OFFICE", "Control Office"),
        ]
        for username, role, department in users:
            user, _ = User.objects.get_or_create(username=username, defaults={
                "email": f"{username}@railnexus.demo", "role": role, "department": department
            })
            user.role, user.department, user.is_staff = role, department, role == "ADMIN"
            user.set_password(password)
            user.save()

        if RailwaySection.objects.exists():
            seed_goods_forecasts(RailwaySection.objects.all(), timezone.localdate())
            self.stdout.write(self.style.SUCCESS("Demo data already exists; demo user passwords refreshed."))
            return

        today = timezone.localdate()
        sections = [
            RailwaySection.objects.create(name="North Gateway Corridor", code="DMD-NGP", start_station="Dharampur", end_station="Nandigram", length=42.5),
            RailwaySection.objects.create(name="River Bridge Corridor", code="NGP-KSV", start_station="Nandigram", end_station="Keshavpur", length=36.2),
            RailwaySection.objects.create(name="Industrial Link", code="KSV-RJN", start_station="Keshavpur", end_station="Raj Nagar", length=28.8, status="RESTRICTED"),
        ]
        asset_specs = [
            ("Bridge Track Circuit", "Track Circuit", 0, "CRITICAL", 5),
            ("Point Machine PM-14", "Point Machine", 0, "DUE", 4),
            ("OHE Mast Group A", "Overhead Equipment", 0, "GOOD", 4),
            ("Rail Weld Cluster", "Track", 1, "DUE", 5),
            ("Axle Counter AC-8", "Axle Counter", 1, "GOOD", 4),
            ("Traction Substation TSS-2", "Power Supply", 1, "GOOD", 5),
            ("Bridge Bearing Set", "Bridge", 2, "UNAVAILABLE", 5),
            ("Signal Relay Room", "Signalling", 2, "GOOD", 4),
            ("OHE Isolator 31", "Overhead Equipment", 2, "DUE", 3),
        ]
        assets = [
            Asset.objects.create(
                name=name, asset_type=kind, section=sections[section],
                health_status=health, criticality=criticality,
                last_maintenance=today - timedelta(days=90),
                next_maintenance=today + timedelta(days=-5 if health in {"DUE", "CRITICAL"} else 30),
            )
            for name, kind, section, health, criticality in asset_specs
        ]
        trains = [
            Train.objects.create(train_number="D101", name="Demo Intercity", train_type="Passenger", priority=5),
            Train.objects.create(train_number="G204", name="Demo Freightliner", train_type="Goods", priority=3),
            Train.objects.create(train_number="S318", name="Demo Suburban", train_type="Passenger", priority=4),
            Train.objects.create(train_number="M402", name="Demo Maintenance Consist", train_type="Departmental", priority=2),
        ]
        tomorrow = today + timedelta(days=1)
        schedule_specs = [
            (0, 0, 10, 45, 11, 15), (1, 0, 13, 0, 13, 25),
            (2, 1, 11, 30, 12, 0), (0, 1, 15, 0, 15, 30),
            (1, 2, 9, 30, 10, 0), (2, 2, 16, 0, 16, 30),
        ]
        for train, section, ah, am, dh, dm in schedule_specs:
            TrainSchedule.objects.create(
                train=trains[train], section=sections[section],
                arrival_time=at(tomorrow, ah, am), departure_time=at(tomorrow, dh, dm), date=tomorrow,
            )
        seed_goods_forecasts(sections, today)

        task_specs = [
            ("MX-001", "Emergency track circuit renewal", "ENGINEERING", 0, 0, (5, 5, 5, 5), 90, 1),
            ("MX-002", "Point machine overhaul", "S_AND_T", 0, 1, (5, 5, 5, 4), 60, 1),
            ("MX-003", "OHE contact wire inspection", "TRACTION", 0, 2, (5, 4, 5, 5), 80, 1),
            ("MX-004", "Rail weld ultrasonic testing", "ENGINEERING", 1, 3, (4, 4, 4, 4), 75, -1),
            ("MX-005", "Axle counter calibration", "S_AND_T", 1, 4, (4, 4, 4, 3), 45, 1),
            ("MX-006", "Substation breaker service", "TRACTION", 1, 5, (4, 4, 3, 4), 100, 1),
            ("MX-007", "Bridge bearing inspection", "ENGINEERING", 2, 6, (3, 3, 4, 3), 120, 2),
            ("MX-008", "Relay room preventive checks", "S_AND_T", 2, 7, (3, 3, 2, 3), 50, 2),
            ("MX-009", "Isolator lubrication", "TRACTION", 2, 8, (2, 2, 2, 2), 40, 3),
            ("MX-010", "Routine track geometry check", "ENGINEERING", 1, 3, (1, 2, 1, 2), 45, 4),
        ]
        tasks = []
        for task_id, title, dept, section, asset, factors, duration, offset in task_specs:
            tasks.append(MaintenanceTask.objects.create(
                task_id=task_id, title=title, department=dept, section=sections[section],
                asset=assets[asset], criticality=factors[0], urgency=factors[1],
                safety_risk=factors[2], asset_impact=factors[3],
                estimated_duration=duration, preferred_date=today + timedelta(days=offset),
            ))
        BlockRequest.objects.create(
            maintenance_task=tasks[0], requested_start=at(tomorrow, 10, 30),
            requested_end=at(tomorrow, 12, 0), remarks="Demonstrates a simulated train conflict.",
        )
        BlockRequest.objects.create(
            maintenance_task=tasks[3], requested_start=at(tomorrow, 13, 30),
            requested_end=at(tomorrow, 14, 45), remarks="Available planning window.",
        )

        historical = BlockPlan.objects.create(
            section=sections[1], start_time=at(today - timedelta(days=1), 14),
            end_time=at(today - timedelta(days=1), 15, 30), status="COMPLETED",
            priority_score=76, utilization=84, reason="Completed demonstration maintenance block.",
        )
        BlockPlanTask.objects.create(block_plan=historical, maintenance_task=tasks[9])
        tasks[9].status = "COMPLETED"
        tasks[9].save()
        ExecutionRecord.objects.create(
            block_plan=historical, actual_start=at(today - timedelta(days=1), 14, 10),
            actual_end=at(today - timedelta(days=1), 15, 45), status="DELAYED",
            remarks="Completed with a simulated 15-minute overrun.",
        )
        conflict_plan = BlockPlan.objects.create(
            section=sections[0], start_time=at(tomorrow, 10, 50), end_time=at(tomorrow, 11, 40),
            priority_score=88, utilization=90, reason="Deliberate demo conflict awaiting review.",
        )
        Conflict.objects.create(
            block_plan=conflict_plan, conflict_type="TRAIN_VS_BLOCK",
            description="Conflicts with simulated Demo Intercity movement.", severity="HIGH",
        )
        alerts = [
            ("Critical maintenance due", "Bridge Track Circuit requires urgent attention.", "CRITICAL"),
            ("Overdue task", "MX-004 is beyond its preferred maintenance date.", "HIGH"),
            ("Train conflict detected", "A requested window overlaps Demo Intercity.", "HIGH"),
            ("Simulated data active", "All operational data in this prototype is simulated.", "LOW"),
        ]
        Alert.objects.bulk_create([Alert(title=t, message=m, severity=s) for t, m, s in alerts])
        self.stdout.write(self.style.SUCCESS("RailNexus simulated demo data created."))
        self.stdout.write(f"Demo password for all users: {password}")
