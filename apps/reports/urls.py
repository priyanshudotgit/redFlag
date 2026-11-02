"""URL configuration for reports app."""

from django.urls import path
from apps.reports import views

urlpatterns = [
    path('new/', views.submit_report, name='report_submit'),
    path('ack/<str:reference_id>/', views.report_acknowledgement, name='report_acknowledgement'),
    path('track/', views.track_report, name='report_track'),
    path('view/<str:reference_id>/', views.report_detail, name='report_detail'),
]

