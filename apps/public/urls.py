"""URL configuration for public app."""

from django.urls import path
from apps.public import views

urlpatterns = [
    path('', views.home, name='home'),
    path('how-it-works/', views.how_it_works, name='how_it_works'),
    path('helpline/', views.helpline, name='helpline'),
    path('transparency/', views.transparency, name='transparency'),
    path('privacy/', views.privacy_policy, name='privacy'),
    path('terms/', views.terms_of_service, name='terms'),
]

