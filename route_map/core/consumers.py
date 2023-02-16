import json
from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
from django.core.serializers.json import DjangoJSONEncoder
from django.forms.models import model_to_dict
from map.models import City, Route



class RouteConsumer(WebsocketConsumer):
    def get_cities(self, data):
        cities = {}

        for city in City.objects.all():
            cities[city.id] = model_to_dict(city)

        self.send_individual_data("setCities", cities)  # we don't need to send the cities to all the open tabs

    def get_routes(self, data):
        city_id = data["city"]
        routes_info = {}

        routes = Route.objects.filter(city=city_id, is_active=True)
        for route in routes:
            stops = route.stops.filter(is_active=True)
            routes_info[route.id] = model_to_dict(route)
            routes_info[route.id]["stops"] = []
            for stop in stops:
                routes_info[route.id]["stops"].append([stop.station.point.y, stop.station.point.x])

        message = {
            "city": city_id,
            "routes": routes_info
        }

        self.send_individual_data("setRoutes", message)  # we don't need to send the routes to all the open tabs

    def connect(self):
        # Join routes group
        async_to_sync(self.channel_layer.group_add)(
            "routes",
            self.channel_name
        )

        self.accept()

    def disconnect(self, close_code):
        # Leave routes group
        async_to_sync(self.channel_layer.group_discard)(
            "routes",
            self.channel_name
        )

    commands = {
        "get_cities": get_cities,
        "get_routes": get_routes
    }

    # Receive message from WebSocket
    def receive(self, text_data):
        data = json.loads(text_data)
        command = data["command"]
        self.commands[command](self, data)

    # Receive message to handle in consumers
    def new_data(self, event):
        data = event["data"]
        # Send query to WebSocket
        self.send(text_data=data)

    def send_individual_data(self, call, data):
        # Send data to specific user's group
        self.send(json.dumps(
            {
                "type": "new_data",
                "call": call,
                "data": data
            },
            cls=DjangoJSONEncoder
        ))


    def send_shared_data(self, data, channel_name="routes"):
        # Send data to all users in 'routes' group
        async_to_sync(self.channel_layer.group_send)(
            channel_name,
            {
                "type": "new_data",
                "data": json.dumps(data, cls=DjangoJSONEncoder)
            }
        )