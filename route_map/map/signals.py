import json
from django.contrib.gis.geos import Point
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models.signals import pre_save, post_save, post_delete
from django.dispatch import receiver
from django.forms.models import model_to_dict
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from .models import Station, Route, Stop


def send_to_ws(data):
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        "routes",
        {
            "type": "new_data",
            "data": json.dumps(data, cls=DjangoJSONEncoder)
        }
    )

def gen_route_info(route):
    route_info = model_to_dict(route)
    stops = route.stops.filter(is_active=True)
    route_info["stops"] = []
    for stop in stops:
        route_info["stops"].append([stop.station.point.y, stop.station.point.x])
    return route_info


def reload_route(route):
    data = {
        "data": gen_route_info(route),
        "call": "reloadRoute",
        "actionTag": "routeChange"
    }
    send_to_ws(data)


@receiver(pre_save, sender=Station)
def pre_save_station(sender, instance, **kwargs):
    """
    We need this to determine what fields have changed in the upgrade.
    """
    try:
        instance._pre_save_instance = Station.objects.get(pk=instance.pk)
    except Station.DoesNotExist:
        instance._pre_save_instance = instance


@receiver(post_save, sender=Station)
def generate_station_point(sender, instance, created, **kwargs):
    """
    Signal to automatically fill point field on Station objects
    """
    station = instance
    prev_station = station._pre_save_instance

    # checking if lat or lon fields changed
    if station.lat != prev_station.lat or station.lon != prev_station.lon:
        station.point = Point(float(station.lon),
                              float(station.lat))  # for some reason lat and lon are swapped in geodjango
        station.save()


@receiver(pre_save, sender=Route)
def pre_save_route(sender, instance, **kwargs):
    """
    We need this to determine what fields have changed in the upgrade.
    """
    try:
        instance._pre_save_instance = Route.objects.get(pk=instance.pk)
    except Route.DoesNotExist:
        instance._pre_save_instance = instance


@receiver(post_save, sender=Route)
def change_route_status(sender, instance, created, **kwargs):
    """
    Signal that triggers websocket if route becomes active/inactive
    """
    route = instance
    prev_route = route._pre_save_instance

    if prev_route.is_active and not route.is_active:
        data = {
            "data": route.id,
            "call": "disableRoute",
            "actionTag": "routeChange"
        }
        send_to_ws(data)
    if not prev_route.is_active and route.is_active:
        data = {
            "data": gen_route_info(route),
            "call": "enableRoute",
            "actionTag": "routeChange"
        }
        send_to_ws(data)


@receiver(post_delete, sender=Route)
def remove_route_on_deletion(sender, instance, **kwargs):
    """
    Signal that triggers websocket to reload route on map if route gets deleted
    """
    route = instance

    if route.is_active:
        data = {
            "data": route.id,
            "call": "disableRoute",
            "actionTag": "routeChange"
        }
        send_to_ws(data)


@receiver(pre_save, sender=Stop)
def pre_save_stop(sender, instance, **kwargs):
    """
    We need this to determine what fields have changed in the upgrade.
    """
    try:
        instance._pre_save_instance = Stop.objects.get(pk=instance.pk)
    except Stop.DoesNotExist:
        instance._pre_save_instance = instance


@receiver(post_save, sender=Stop)
def update_route_stops(sender, instance, created, **kwargs):
    """
    Signal that triggers websocket to reload route if stop data changed
    """
    stop = instance
    prev_stop = stop._pre_save_instance

    if created and stop.is_active:
        if stop.route.is_active:
            reload_route(stop.route)

    trigger_fields = [
        "index",
        "is_active",
        "route",
        "station"
    ]

    # If any of the trigger fields changed, we're reloading the route
    for field in trigger_fields:
        if getattr(stop, field) != getattr(prev_stop, field):
            if stop.route.is_active and (stop.is_active or field == "is_active"):
                reload_route(stop.route)
            # And, additionally we need to reload the other route, if the stop has switched routes
            if field == "route" and prev_stop.route.is_active:
                reload_route(prev_stop.route)


@receiver(post_delete, sender=Stop)
def remove_stop_on_deletion(sender, instance, **kwargs):
    """
    Signal that triggers websocket to reload route if stop is deleted
    """
    stop = instance

    if stop.is_active and stop.route.is_active:
        reload_route(stop.route)


@receiver(post_save, sender=Station)
def update_route_stations(sender, instance, created, **kwargs):
    """
    Signal that triggers websocket to reload route if station coordinates changed
    """
    station = instance
    prev_station = station._pre_save_instance

    trigger_fields = [
        "lat",
        "lon",
        "point"
    ]

    # If any of the trigger fields changed, we're reloading the route
    for field in trigger_fields:
        if getattr(station, field) != getattr(prev_station, field):
            routes = {}
            for stop in station.stops.filter(is_active=True):
                route = stop.route
                if route.id not in routes and route.is_active:
                    routes[route.id] = route

            for id in routes:
                reload_route(routes[id])