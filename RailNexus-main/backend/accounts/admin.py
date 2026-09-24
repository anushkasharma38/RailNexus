from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from maintenance.models import Alert, BlockRequest, ExecutionRecord, MaintenanceTask
from planning.models import BlockPlan, BlockPlanTask, Conflict
from railway.models import Asset, RailwaySection, Train, TrainSchedule
from .models import User


@admin.register(User)
class RailNexusUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (("RailNexus role", {"fields": ("role", "department")}),)
    add_fieldsets = UserAdmin.add_fieldsets + (("RailNexus role", {"fields": ("role", "department")}),)


for model in [
    RailwaySection, Asset, Train, TrainSchedule, MaintenanceTask, BlockRequest,
    BlockPlan, BlockPlanTask, Conflict, ExecutionRecord, Alert,
]:
    admin.site.register(model)
