"""Root URL configuration for redFlag."""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('apps.public.urls')),
    path('reports/', include('apps.reports.urls')),
    path('accounts/', include('apps.accounts.urls')),
    path('staff/', include('apps.reviews.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

handler403 = 'config.views.custom_403_view'
handler404 = 'config.views.custom_404_view'
handler500 = 'config.views.custom_500_view'

