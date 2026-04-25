from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('cosecha/<int:pk>/', views.detalle_cosecha, name='detalle_cosecha'),
    path('dashboard/', views.dashboard, name='dashboard'),
]