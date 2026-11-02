"""Views for authentication and user accounts."""

from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.http import url_has_allowed_host_and_scheme
from apps.accounts.forms import UserRegistrationForm, UserLoginForm
from apps.reports.models import Report

def login_view(request):
    """Unified secure login for citizens and departmental officers."""
    if request.user.is_authenticated:
        if request.user.is_staff:
            return redirect('staff_queue')
        return redirect('dashboard')

    redirect_to = request.POST.get('next') or request.GET.get('next') or ''

    if request.method == 'POST':
        form = UserLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"Welcome back, {user.username}.")

            # Safe redirect check
            if redirect_to and url_has_allowed_host_and_scheme(
                url=redirect_to,
                allowed_hosts={request.get_host()},
                require_https=request.is_secure()
            ):
                return redirect(redirect_to)

            if user.is_staff:
                return redirect('staff_queue')
            return redirect('dashboard')
        else:
            messages.error(request, "Invalid username or password. Please verify your credentials.")
    else:
        form = UserLoginForm(request)

    return render(request, 'accounts/login.html', {
        'form': form,
        'next': redirect_to
    })


def register_view(request):
    """Citizen account creation."""
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Your account has been created successfully.")
            return redirect('dashboard')
        else:
            messages.error(request, "Please correct the errors in the form below.")
    else:
        form = UserRegistrationForm()

    return render(request, 'accounts/register.html', {'form': form})


def logout_view(request):
    """Secure session termination."""
    if request.method == 'POST' or request.method == 'GET':
        logout(request)
        messages.info(request, "You have been securely logged out.")
    return redirect('home')


@login_required
def dashboard_view(request):
    """Authenticated user dashboard displaying only reports submitted by the user."""
    user_reports = Report.objects.filter(reporter=request.user).order_by('-created_at')

    # Summary metrics
    metrics = {
        'total': user_reports.count(),
        'pending': user_reports.filter(status__in=['submitted', 'under_review']).count(),
        'investigating': user_reports.filter(status='investigating').count(),
        'resolved': user_reports.filter(status='resolved').count(),
    }

    return render(request, 'accounts/dashboard.html', {
        'reports': user_reports,
        'metrics': metrics,
    })

