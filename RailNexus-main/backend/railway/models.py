from django.db import models


class RailwaySection(models.Model):
    class Status(models.TextChoices):
        AVAILABLE = "AVAILABLE", "Available"
        RESTRICTED = "RESTRICTED", "Restricted"
        CLOSED = "CLOSED", "Closed"

    name = models.CharField(max_length=120)
    code = models.CharField(max_length=20, unique=True)
    start_station = models.CharField(max_length=80)
    end_station = models.CharField(max_length=80)
    length = models.DecimalField(max_digits=7, decimal_places=2)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.AVAILABLE)

    def __str__(self):
        return f"{self.code}: {self.start_station}–{self.end_station}"


class Asset(models.Model):
    class Health(models.TextChoices):
        GOOD = "GOOD", "Good"
        DUE = "DUE", "Maintenance Due"
        CRITICAL = "CRITICAL", "Critical"
        UNAVAILABLE = "UNAVAILABLE", "Unavailable"

    name = models.CharField(max_length=120)
    asset_type = models.CharField(max_length=80)
    section = models.ForeignKey(RailwaySection, on_delete=models.CASCADE, related_name="assets")
    health_status = models.CharField(max_length=16, choices=Health.choices)
    criticality = models.PositiveSmallIntegerField(default=3)
    last_maintenance = models.DateField(null=True, blank=True)
    next_maintenance = models.DateField(null=True, blank=True)

    def __str__(self):
        return self.name


class Train(models.Model):
    train_number = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=120)
    train_type = models.CharField(max_length=40)
    priority = models.PositiveSmallIntegerField(default=3)

    def __str__(self):
        return f"{self.train_number} {self.name}"


class TrainSchedule(models.Model):
    train = models.ForeignKey(Train, on_delete=models.CASCADE, related_name="schedules")
    section = models.ForeignKey(RailwaySection, on_delete=models.CASCADE, related_name="schedules")
    arrival_time = models.DateTimeField()
    departure_time = models.DateTimeField()
    date = models.DateField()

    class Meta:
        ordering = ["arrival_time"]
        indexes = [models.Index(fields=["section", "date"])]


class GoodsTrainForecast(models.Model):
    class Level(models.TextChoices):
        LOW = "LOW", "Low"
        MEDIUM = "MEDIUM", "Medium"
        HIGH = "HIGH", "High"

    date = models.DateField()
    section = models.ForeignKey(RailwaySection, on_delete=models.CASCADE, related_name="goods_forecasts")
    expected_train_count = models.PositiveIntegerField()
    forecast_level = models.CharField(max_length=8, choices=Level.choices)

    class Meta:
        ordering = ["date", "section"]
        constraints = [
            models.UniqueConstraint(fields=["date", "section"], name="unique_goods_forecast_per_section_date")
        ]
        indexes = [models.Index(fields=["section", "date"])]
