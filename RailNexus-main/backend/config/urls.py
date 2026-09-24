from django.contrib import admin
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from accounts.views import LoginView, LogoutView, MeView
from analytics.views import AnalyticsView, BottleneckView, DashboardView, PlanningCalendarView, ReportsView
from maintenance.views import (
    AlertViewSet,
    BlockRequestViewSet,
    ExecutionRecordViewSet,
    MaintenanceTaskViewSet,
)
from planning.views import BlockPlanViewSet, ConflictViewSet, PlanningViewSet
from railway.views import (
    AssetViewSet,
    GoodsTrainForecastViewSet,
    RailwaySectionViewSet,
    TrainScheduleViewSet,
    TrainViewSet,
)


router = DefaultRouter()
router.register("sections", RailwaySectionViewSet)
router.register("assets", AssetViewSet)
router.register("trains", TrainViewSet)
router.register("schedules", TrainScheduleViewSet)
router.register("goods-forecasts", GoodsTrainForecastViewSet)
router.register("tasks", MaintenanceTaskViewSet)
router.register("block-requests", BlockRequestViewSet)
router.register("block-plans", BlockPlanViewSet)
router.register("conflicts", ConflictViewSet)
router.register("execution", ExecutionRecordViewSet)
router.register("alerts", AlertViewSet)
router.register("planning", PlanningViewSet, basename="planning")

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/login/", LoginView.as_view()),
    path("api/auth/logout/", LogoutView.as_view()),
    path("api/auth/me/", MeView.as_view()),
    path("api/dashboard/", DashboardView.as_view()),
    path("api/analytics/", AnalyticsView.as_view()),
    path("api/bottlenecks/", BottleneckView.as_view()),
    path("api/calendar/", PlanningCalendarView.as_view()),
    path("api/reports/", ReportsView.as_view()),
    path("api/", include(router.urls)),
]
