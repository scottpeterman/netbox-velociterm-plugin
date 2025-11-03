from django.urls import path
from . import views

urlpatterns = [
    path('device/<int:pk>/', views.device_terminal_view, name='device_terminal'),
]
