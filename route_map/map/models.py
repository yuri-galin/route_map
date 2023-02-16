from django.db import models
from django.contrib.gis.db.models import PointField
from django.contrib.gis.geos import Point


class City(models.Model):
    title = models.CharField(max_length=100)  # should check the longest station name
    lower_bound_lat = models.DecimalField(max_digits=9, decimal_places=6)
    lower_bound_lon = models.DecimalField(max_digits=9, decimal_places=6)
    upper_bound_lat = models.DecimalField(max_digits=9, decimal_places=6)
    upper_bound_lon = models.DecimalField(max_digits=9, decimal_places=6)

    def __str__(self):
        return f"ID {self.id} — {self.title}"

    class Meta:
        ordering = ["title",]
        verbose_name = "City"
        verbose_name_plural = "Cities"


class Station(models.Model):
    title = models.CharField(max_length=100)  # should check the longest station name
    address = models.CharField(max_length=175)
    lat = models.DecimalField(max_digits=9, decimal_places=6)
    lon = models.DecimalField(max_digits=9, decimal_places=6)
    point = PointField(blank=True)

    def save(self, *args, **kwargs):
        # on creation we automatically fill point field using lat and lon values
        # update of this field according to lat and lon gets handled in signals
        if self.pk is None:
            self.point = Point(float(self.lon),
                               float(self.lat))  # for some reason lat and lon are swapped in geodjango
        super(Station, self).save(*args, **kwargs)

    def __str__(self):
        return f"ID {self.id} — {self.title}"


class Route(models.Model):
    city = models.ForeignKey(City, related_name="routes", on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    number = models.CharField(max_length=50, unique=True)  # idk how the route numbers are formed, so I chose 50 chars to be safe
    is_active = models.BooleanField(null=False, default=True)

    def __str__(self):
        return f"ID {self.id} — {self.title}"

    class Meta:
        ordering = ["number",]


class Stop(models.Model):
    route = models.ForeignKey(Route, related_name="stops", on_delete=models.CASCADE)
    station = models.ForeignKey(Station, related_name="stops", on_delete=models.CASCADE)
    index = models.IntegerField()
    is_active = models.BooleanField(null=False, default=True)

    def __str__(self):
        return f"ID {self.id} — stop {self.station.title} — route {self.route.title}"

    class Meta:
        ordering = ["route", "index"]
        unique_together = ("index", "route",)