"""Custom error handlers for redFlag."""

from django.shortcuts import render

def custom_403_view(request, exception=None):
    """Custom 403 Forbidden page."""
    return render(request, 'errors/403.html', status=403)

def custom_404_view(request, exception=None):
    """Custom 404 Not Found page."""
    return render(request, 'errors/404.html', status=404)

def custom_500_view(request):
    """Custom 500 Server Error page."""
    return render(request, 'errors/500.html', status=500)

