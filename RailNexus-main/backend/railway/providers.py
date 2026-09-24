from abc import ABC, abstractmethod

from maintenance.models import MaintenanceTask
from .models import Asset, GoodsTrainForecast, TrainSchedule


class RailwayDataProvider(ABC):
    """API-ready boundary for approved future railway data integrations."""

    @abstractmethod
    def get_train_schedule(self, section, start, end): ...

    @abstractmethod
    def get_assets(self): ...

    @abstractmethod
    def get_maintenance_tasks(self): ...


class MockRailwayDataProvider(RailwayDataProvider):
    """Reads only local Simulated Railway Data through the Django ORM."""

    def get_train_schedule(self, section, start, end):
        return TrainSchedule.objects.filter(
            section=section, arrival_time__lt=end, departure_time__gt=start
        ).select_related("train")

    def get_assets(self):
        return Asset.objects.select_related("section").all()

    def get_maintenance_tasks(self):
        return MaintenanceTask.objects.select_related("section", "asset").all()


class SimulatedSourceProvider:
    """Marker shared by local adapters; no external railway calls are made."""

    source_label = "SIMULATED RAILWAY DATA"


class TMSDataProvider(SimulatedSourceProvider):
    def get_maintenance_data(self):
        return MaintenanceTask.objects.select_related("section", "asset").all()


class SMMSDataProvider(SimulatedSourceProvider):
    def get_signalling_data(self):
        return MaintenanceTask.objects.filter(department="S_AND_T").select_related("section", "asset")


class TDMSDataProvider(SimulatedSourceProvider):
    def get_traction_asset_data(self):
        return Asset.objects.filter(tasks__department="TRACTION").select_related("section").distinct()


class COADataProvider(SimulatedSourceProvider):
    def get_operational_data(self):
        from planning.models import BlockPlan
        return BlockPlan.objects.select_related("section").prefetch_related("tasks")


class TrainTimetableProvider(SimulatedSourceProvider):
    def get_schedule(self, section=None, date=None):
        schedules = TrainSchedule.objects.select_related("train", "section")
        if section is not None:
            schedules = schedules.filter(section=section)
        if date is not None:
            schedules = schedules.filter(date=date)
        return schedules


class GoodsTrainForecastProvider(SimulatedSourceProvider):
    def get_forecast(self, section=None, date=None):
        forecasts = GoodsTrainForecast.objects.select_related("section")
        if section is not None:
            forecasts = forecasts.filter(section=section)
        if date is not None:
            forecasts = forecasts.filter(date=date)
        return forecasts
