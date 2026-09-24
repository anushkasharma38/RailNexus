from collections import defaultdict
from datetime import datetime, time, timedelta

from django.db import transaction
from django.utils import timezone

from maintenance.models import Alert, BlockRequest, MaintenanceTask
from railway.models import GoodsTrainForecast, RailwaySection, TrainSchedule
from railway.providers import MockRailwayDataProvider
from .models import BlockPlan, BlockPlanTask, Conflict


class PriorityEngine:
    """Explainable prototype scoring; each factor is rated from 1 to 5."""

    WEIGHTS = {
        "criticality": 0.25,
        "urgency": 0.20,
        "safety_risk": 0.25,
        "asset_impact": 0.20,
        "overdue": 0.10,
    }

    def calculate_score(self, task, today=None):
        today = today or timezone.localdate()
        overdue = 5 if task.preferred_date < today else 1
        values = {
            "criticality": task.criticality,
            "urgency": task.urgency,
            "safety_risk": task.safety_risk,
            "asset_impact": task.asset_impact,
            "overdue": overdue,
        }
        score = round(sum(values[key] * weight for key, weight in self.WEIGHTS.items()) / 5 * 100, 1)
        reasons = []
        labels = {
            "criticality": "High asset criticality",
            "urgency": "Urgent maintenance requirement",
            "safety_risk": "High safety risk",
            "asset_impact": "High asset availability impact",
            "overdue": "Maintenance overdue",
        }
        for key, value in values.items():
            if value >= 4:
                reasons.append(labels[key])
        level = "CRITICAL" if score >= 80 else "HIGH" if score >= 65 else "MEDIUM" if score >= 40 else "LOW"
        return {"score": score, "level": level, "reasons": reasons or ["Routine planned maintenance"], "factors": values}


class ConflictDetector:
    def __init__(self, provider=None):
        self.provider = provider or MockRailwayDataProvider()

    @staticmethod
    def overlaps(start_a, end_a, start_b, end_b):
        return start_a < end_b and start_b < end_a

    def train_conflicts(self, section, start, end, schedules=None):
        schedules = schedules if schedules is not None else self.provider.get_train_schedule(section, start, end)
        return [
            {
                "type": "TRAIN_VS_BLOCK",
                "severity": "HIGH",
                "description": f"Conflicts with train {item.train.train_number} ({item.train.name}).",
            }
            for item in schedules
            if self.overlaps(start, end, item.arrival_time, item.departure_time)
        ]

    def block_conflicts(self, section, start, end, exclude_id=None):
        blocks = BlockPlan.objects.filter(
            section=section,
            start_time__lt=end,
            end_time__gt=start,
            status__in=["PENDING_APPROVAL", "APPROVED", "MODIFIED"],
        )
        if exclude_id:
            blocks = blocks.exclude(pk=exclude_id)
        return [{
            "type": "BLOCK_VS_BLOCK",
            "severity": "CRITICAL",
            "description": f"Overlaps existing block plan #{block.id}.",
        } for block in blocks]

    def detect(self, section, start, end, exclude_id=None):
        if end <= start:
            return [{"type": "INVALID_TIME", "severity": "CRITICAL", "description": "End time must be after start time."}]
        if section.status != "AVAILABLE":
            return [{"type": "SECTION_AVAILABILITY", "severity": "HIGH", "description": f"Section is {section.status.lower()}."}]
        return self.train_conflicts(section, start, end) + self.block_conflicts(section, start, end, exclude_id)


class BlockOptimizer:
    SLOT_MINUTES = 30

    def __init__(self):
        self.priority = PriorityEngine()
        self.conflicts = ConflictDetector()

    @staticmethod
    def _asset_window_score(tasks, start, day_start):
        impact = max(task.asset_impact for task in tasks)
        criticality = max((task.asset.criticality if task.asset else task.criticality) for task in tasks)
        health_bonus = max(
            {"UNAVAILABLE": 25, "CRITICAL": 20, "DUE": 10, "GOOD": 0}.get(
                task.asset.health_status if task.asset else "GOOD", 0
            )
            for task in tasks
        )
        delay_hours = max((start - day_start).total_seconds() / 3600, 0)
        return round(impact * 12 + criticality * 8 + health_bonus - delay_hours * (impact + criticality), 2)

    @staticmethod
    def _forecast_buffer(section, task_date):
        level = GoodsTrainForecast.objects.filter(section=section, date=task_date).values_list(
            "forecast_level", flat=True
        ).first()
        return level, {"HIGH": 30, "MEDIUM": 15}.get(level, 0)

    def _window(self, tasks, requested_start=None):
        task_date = (
            timezone.localtime(requested_start).date()
            if requested_start
            else max(tasks[0].preferred_date, timezone.localdate())
        )
        start = requested_start or timezone.make_aware(datetime.combine(task_date, time(9, 0)))
        duration = max(task.estimated_duration for task in tasks)
        latest = timezone.make_aware(datetime.combine(task_date, time(22, 0)))
        original = start
        day_start = start
        forecast_level, traffic_buffer = self._forecast_buffer(tasks[0].section, task_date)
        candidates = []
        while start + timedelta(minutes=duration) <= latest:
            end = start + timedelta(minutes=duration)
            forecast_conflict = False
            if traffic_buffer:
                buffered_start = start - timedelta(minutes=traffic_buffer)
                buffered_end = end + timedelta(minutes=traffic_buffer)
                forecast_conflict = bool(
                    self.conflicts.train_conflicts(tasks[0].section, buffered_start, buffered_end)
                )
            if not self.conflicts.detect(tasks[0].section, start, end) and not forecast_conflict:
                candidates.append((self._asset_window_score(tasks, start, day_start), start, end))
            start += timedelta(minutes=self.SLOT_MINUTES)
        if not candidates:
            return None, None, False, ""
        _, selected_start, selected_end = max(candidates, key=lambda item: item[0])
        reasons = []
        if any(
            task.asset_impact >= 4
            or (task.asset and task.asset.criticality >= 4)
            or (task.asset and task.asset.health_status in {"CRITICAL", "UNAVAILABLE"})
            for task in tasks
        ):
            reasons.append("Window selected early to minimize critical asset downtime.")
        if forecast_level in {"HIGH", "MEDIUM"}:
            reasons.append(
                f"Simulated {forecast_level} goods train forecast applied a {traffic_buffer}-minute traffic buffer."
            )
        return selected_start, selected_end, original != selected_start, " ".join(reasons)

    @transaction.atomic
    def generate(self, task_ids=None):
        locked_tasks = MaintenanceTask.objects.select_for_update().filter(
            status__in=["PENDING", "REQUESTED"]
        )
        if task_ids:
            locked_tasks = locked_tasks.filter(id__in=task_ids)
        locked_ids = list(locked_tasks.values_list("id", flat=True))
        tasks = MaintenanceTask.objects.filter(id__in=locked_ids).select_related("section", "asset")
        ranked = sorted(tasks, key=lambda task: self.priority.calculate_score(task)["score"], reverse=True)
        groups = defaultdict(list)
        for task in ranked:
            groups[(task.section_id, task.preferred_date)].append(task)

        plans = []
        for compatible in groups.values():
            request = BlockRequest.objects.filter(maintenance_task__in=compatible, status="PENDING").order_by("requested_start").first()
            requested_start = request.requested_start if request else None
            start, end, shifted, window_reason = self._window(compatible, requested_start)
            if not start:
                Alert.objects.create(
                    title="Planning window unavailable",
                    message=f"No conflict-free window found for {compatible[0].section.name}.",
                    severity="HIGH",
                )
                continue
            scores = [self.priority.calculate_score(task)["score"] for task in compatible]
            departments = sorted({task.get_department_display() for task in compatible})
            reason = f"{len(compatible)} maintenance activities coordinated into one block ({', '.join(departments)})."
            if shifted:
                reason += " Original window conflicted with a scheduled train movement or existing block."
            if window_reason:
                reason += f" {window_reason}"
            plan = BlockPlan.objects.create(
                section=compatible[0].section,
                start_time=start,
                end_time=end,
                priority_score=max(scores),
                utilization=round(sum(task.estimated_duration for task in compatible) / (len(compatible) * max(task.estimated_duration for task in compatible)) * 100, 1),
                reason=reason,
            )
            BlockPlanTask.objects.bulk_create([
                BlockPlanTask(block_plan=plan, maintenance_task=task) for task in compatible
            ])
            for task in compatible:
                task.status = "PLANNED"
                task.save(update_fields=["status"])
            BlockRequest.objects.filter(maintenance_task__in=compatible, status="PENDING").update(status="PLANNED")
            plans.append(plan)
        return plans


class BottleneckDetector:
    """Explainable section/day pressure detector for simulated planning data."""

    SLOT_MINUTES = 30
    DAY_START = time(9, 0)
    DAY_END = time(22, 0)

    def detect(self, start_date=None, end_date=None, sections=None):
        start_date = start_date or timezone.localdate()
        end_date = end_date or start_date + timedelta(days=6)
        sections = sections if sections is not None else RailwaySection.objects.all()
        severity_rank = {"HIGH": 3, "MEDIUM": 2, "LOW": 1}
        rows = []
        day = start_date
        while day <= end_date:
            day_start = timezone.make_aware(datetime.combine(day, self.DAY_START))
            day_end = timezone.make_aware(datetime.combine(day, self.DAY_END))
            for section in sections:
                schedules = list(TrainSchedule.objects.filter(section=section, date=day))
                blocks = list(BlockPlan.objects.filter(
                    section=section,
                    start_time__lt=day_end,
                    end_time__gt=day_start,
                ).exclude(status="REJECTED"))
                demand = MaintenanceTask.objects.filter(
                    section=section,
                    preferred_date=day,
                ).exclude(status="COMPLETED").count()
                conflict_count = Conflict.objects.filter(
                    block_plan__section=section,
                    block_plan__start_time__date=day,
                    resolved=False,
                ).count()
                total_windows = int((day_end - day_start).total_seconds() / 60 / self.SLOT_MINUTES)
                available_windows = 0
                candidate = day_start
                while candidate < day_end:
                    candidate_end = candidate + timedelta(minutes=self.SLOT_MINUTES)
                    occupied = section.status != "AVAILABLE" or any(
                        ConflictDetector.overlaps(
                            candidate, candidate_end, item.arrival_time, item.departure_time
                        )
                        for item in schedules
                    ) or any(
                        ConflictDetector.overlaps(
                            candidate, candidate_end, block.start_time, block.end_time
                        )
                        for block in blocks
                    )
                    if not occupied:
                        available_windows += 1
                    candidate = candidate_end
                blocked_periods = total_windows - available_windows
                pressure = conflict_count * 2 + demand + len(schedules) + min(blocked_periods, 5)
                severity = "HIGH" if pressure >= 10 or available_windows <= 2 else "MEDIUM" if pressure >= 5 else "LOW"
                reasons = [
                    f"{demand} maintenance request(s)",
                    f"{len(schedules)} train movement(s)",
                    f"{available_windows} of {total_windows} maintenance windows available",
                ]
                if conflict_count:
                    reasons.append(f"{conflict_count} unresolved conflict(s)")
                rows.append({
                    "section": section.name,
                    "section_code": section.code,
                    "date": day,
                    "severity": severity,
                    "reason": reasons,
                    "conflict_count": conflict_count,
                    "maintenance_demand": demand,
                    "train_traffic": len(schedules),
                    "available_windows": available_windows,
                    "blocked_periods": blocked_periods,
                })
            day += timedelta(days=1)
        return sorted(
            rows,
            key=lambda row: (
                -severity_rank[row["severity"]],
                row["available_windows"],
                -row["maintenance_demand"],
                row["section"],
            ),
        )


class ScenarioSimulator:
    def simulate(self, plan, train_delay=0, duration_change=0, start_shift=0):
        before_conflicts = ConflictDetector().detect(plan.section, plan.start_time, plan.end_time, plan.id)
        proposed_start = plan.start_time + timedelta(minutes=start_shift)
        proposed_end = plan.end_time + timedelta(minutes=start_shift + duration_change)
        schedules = list(TrainSchedule.objects.filter(section=plan.section).select_related("train"))
        for schedule in schedules:
            schedule.arrival_time += timedelta(minutes=train_delay)
            schedule.departure_time += timedelta(minutes=train_delay)
        detector = ConflictDetector()
        if proposed_end <= proposed_start:
            after_conflicts = [{
                "type": "INVALID_TIME",
                "severity": "CRITICAL",
                "description": "End time must be after start time.",
            }]
        elif plan.section.status != "AVAILABLE":
            after_conflicts = [{
                "type": "SECTION_AVAILABILITY",
                "severity": "HIGH",
                "description": f"Section is {plan.section.status.lower()}.",
            }]
        else:
            after_conflicts = detector.train_conflicts(
                plan.section, proposed_start, proposed_end, schedules
            )
            after_conflicts += detector.block_conflicts(
                plan.section, proposed_start, proposed_end, plan.id
            )
        duration = max((proposed_end - proposed_start).total_seconds() / 60, 1)
        workload = sum(task.estimated_duration for task in plan.tasks.all())
        task_count = plan.tasks.count()
        proposed_utilization = round(min(workload / (task_count * duration) * 100, 100), 1) if task_count else 0
        assets = plan.section.assets.all()
        asset_total = assets.count()
        availability = round(assets.exclude(health_status="UNAVAILABLE").count() / asset_total * 100, 1) if asset_total else 100
        return {
            "before": {"start": plan.start_time, "end": plan.end_time, "conflicts": len(before_conflicts), "availability": availability, "utilization": float(plan.utilization), "tasks_completed": task_count},
            "after": {"start": proposed_start, "end": proposed_end, "conflicts": len(after_conflicts), "availability": availability, "utilization": proposed_utilization, "tasks_completed": task_count if not after_conflicts else 0},
            "conflict_details": after_conflicts,
        }


class ReplanningService:
    @transaction.atomic
    def replan(self, plan, train_delay=30):
        before = {"start": plan.start_time, "end": plan.end_time}
        schedules = TrainSchedule.objects.filter(section=plan.section)
        affected = schedules.filter(arrival_time__lt=plan.end_time, departure_time__gt=plan.start_time - timedelta(minutes=train_delay))
        if not affected.exists():
            return {
                "before": before,
                "after": before.copy(),
                "reason": "No train movement was affected; the block window was unchanged.",
            }
        for schedule in affected:
            schedule.arrival_time += timedelta(minutes=train_delay)
            schedule.departure_time += timedelta(minutes=train_delay)
            schedule.date = schedule.arrival_time.date()
            schedule.save()
        duration = int((plan.end_time - plan.start_time).total_seconds() / 60)
        candidate = plan.start_time
        plan_date = timezone.localtime(plan.start_time).date()
        latest = timezone.make_aware(datetime.combine(plan_date, time(22, 0)))
        detector = ConflictDetector()
        while candidate + timedelta(minutes=duration) <= latest:
            if not detector.detect(plan.section, candidate, candidate + timedelta(minutes=duration), plan.id):
                break
            candidate += timedelta(minutes=30)
        else:
            raise ValueError("No conflict-free replanning window is available before 22:00.")
        plan.start_time = candidate
        plan.end_time = candidate + timedelta(minutes=duration)
        plan.status = "MODIFIED"
        plan.reason += f" Replanned after simulated {train_delay}-minute train delay."
        plan.save()
        Alert.objects.create(title="Block replanned", message=f"Plan #{plan.id} moved to avoid a simulated train conflict.", severity="MEDIUM")
        return {"before": before, "after": {"start": plan.start_time, "end": plan.end_time}, "reason": "Train movement conflict introduced; next conflict-free window selected."}
