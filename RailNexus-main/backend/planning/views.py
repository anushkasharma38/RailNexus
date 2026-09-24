from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ViewSet

from accounts.permissions import RoleWritePermission
from .models import BlockPlan, Conflict
from .serializers import BlockPlanSerializer, ConflictSerializer
from .services import BlockOptimizer, ConflictDetector, ReplanningService, ScenarioSimulator


def request_integer(request, key, default=None, minimum=None):
    value = request.data.get(key, default)
    try:
        value = int(value)
    except (TypeError, ValueError):
        raise ValidationError({key: "Must be an integer."})
    if minimum is not None and value < minimum:
        raise ValidationError({key: f"Must be at least {minimum}."})
    return value


def requested_plan(request):
    plan_id = request.data.get("plan_id")
    if not plan_id:
        raise ValidationError({"plan_id": "This field is required."})
    return get_object_or_404(BlockPlan.objects.select_related("section"), pk=plan_id)


class BlockPlanViewSet(ModelViewSet):
    permission_classes = [RoleWritePermission]
    queryset = BlockPlan.objects.select_related("section").prefetch_related("tasks", "conflicts").all()
    serializer_class = BlockPlanSerializer

    @action(detail=True, methods=["post"])
    def review(self, request, pk=None):
        plan = self.get_object()
        decision = request.data.get("decision")
        if request.user.role not in {"ADMIN", "CONTROL_OFFICE"}:
            return Response({"detail": "Control Office or Admin role required."}, status=status.HTTP_403_FORBIDDEN)
        valid = {"approve": "APPROVED", "modify": "MODIFIED", "reject": "REJECTED"}
        if decision not in valid:
            return Response({"detail": "Decision must be approve, modify, or reject."}, status=400)
        conflicts = ConflictDetector().detect(plan.section, plan.start_time, plan.end_time, plan.id)
        if decision == "approve" and conflicts:
            return Response({"detail": "Resolve displayed conflicts before approval.", "conflicts": conflicts}, status=400)
        if decision == "modify":
            serializer = self.get_serializer(plan, data=request.data.get("changes", {}), partial=True)
            serializer.is_valid(raise_exception=True)
            proposed_start = serializer.validated_data.get("start_time", plan.start_time)
            proposed_end = serializer.validated_data.get("end_time", plan.end_time)
            proposed_conflicts = ConflictDetector().detect(plan.section, proposed_start, proposed_end, plan.id)
            if proposed_conflicts:
                return Response({"detail": "Proposed modification has conflicts.", "conflicts": proposed_conflicts}, status=400)
            serializer.save(status="MODIFIED")
        else:
            plan.status = valid[decision]
            plan.save(update_fields=["status"])
        return Response(self.get_serializer(plan).data)


class ConflictViewSet(ModelViewSet):
    permission_classes = [RoleWritePermission]
    queryset = Conflict.objects.select_related("block_plan", "block_request").order_by("-created_at")
    serializer_class = ConflictSerializer


class PlanningViewSet(ViewSet):
    permission_classes = [RoleWritePermission]

    @action(detail=False, methods=["post"])
    def run(self, request):
        plans = BlockOptimizer().generate(request.data.get("task_ids"))
        return Response(BlockPlanSerializer(plans, many=True).data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["post"])
    def simulate(self, request):
        plan = requested_plan(request)
        result = ScenarioSimulator().simulate(
            plan,
            request_integer(request, "train_delay", 0, 0),
            request_integer(request, "duration_change", 0),
            request_integer(request, "start_shift", 0),
        )
        return Response(result)

    @action(detail=False, methods=["post"])
    def replan(self, request):
        plan = requested_plan(request)
        try:
            result = ReplanningService().replan(
                plan, request_integer(request, "train_delay", 30, 0)
            )
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(result)

    @action(detail=False, methods=["post"])
    def detect(self, request):
        plan = requested_plan(request)
        conflicts = ConflictDetector().detect(plan.section, plan.start_time, plan.end_time, plan.id)
        return Response({"count": len(conflicts), "conflicts": conflicts})
