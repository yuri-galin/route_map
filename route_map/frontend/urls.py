from django.urls import path
from . import views

urlpatterns = [
    path('routes/map/', views.routes_map, name="routes_map"),
]
