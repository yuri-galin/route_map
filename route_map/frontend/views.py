from django.shortcuts import render
from map.models import City

# Create your views here.

def routes_map(request):
    cities = City.objects.all()
    return render(request, 'routes_map.html', {"cities": cities})