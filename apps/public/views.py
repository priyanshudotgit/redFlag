"""Views for public informative screens and civic transparency analytics."""

from django.shortcuts import render
from django.db.models import Count
from apps.reports.models import Report

def home(request):
    """Public landing page highlighting civic purpose, transparency, and reporting access."""
    # Compute genuine real-time database counts
    metrics = {
        'total_reports': Report.objects.count(),
        'resolved_cases': Report.objects.filter(status='resolved').count(),
        'active_investigations': Report.objects.filter(status__in=['under_review', 'investigating']).count(),
    }

    # Latest resolved cases (strictly sanitized: category, reference ID, resolution date, outcome note)
    recent_resolutions = Report.objects.filter(status='resolved').order_by('-updated_at')[:4]

    return render(request, 'public/home.html', {
        'metrics': metrics,
        'recent_resolutions': recent_resolutions,
    })


def how_it_works(request):
    """Standard operating procedures for lodging complaints, triage, and tracking."""
    return render(request, 'public/how_it_works.html')


def helpline(request):
    """Emergency and distress helpline directory."""
    agencies = [
        {
            'name': 'National Emergency Response (All Hazards)',
            'number': '112',
            'desc': 'Unified 24x7 emergency helpline for police, fire, and medical dispatch.',
            'category': 'Emergency'
        },
        {
            'name': 'National Child Helpline',
            'number': '1098',
            'desc': 'Toll-free emergency outreach service for children in distress and victims of child abuse.',
            'category': 'Child Safety'
        },
        {
            'name': "Women's Distress Helpline",
            'number': '1091',
            'desc': 'Crisis intervention, psychological counseling, and legal assistance for domestic abuse or harassment.',
            'category': 'Women Safety'
        },
        {
            'name': 'National Cyber Crime Reporting Portal',
            'number': '1930',
            'desc': 'Financial cyber fraud, digital extortion, online stalking, and identity theft response.',
            'category': 'Cyber Safety'
        },
        {
            'name': 'Central Vigilance / Anti-Corruption Wing',
            'number': '1064',
            'desc': 'Whistleblower reporting against public sector bribery, extortion, or abuse of power.',
            'category': 'Public Integrity'
        },
        {
            'name': 'National Anti-Trafficking Bureau',
            'number': '1800-11-2000',
            'desc': 'Confidential tip line for human trafficking and forced labor operations.',
            'category': 'Trafficking'
        },
    ]
    return render(request, 'public/helpline.html', {'agencies': agencies})


def transparency(request):
    """Aggregate civic reporting statistics and outcome analytics."""
    total_count = Report.objects.count()
    status_counts = dict(Report.objects.values('status').annotate(count=Count('id')).values_list('status', 'count'))
    category_counts = Report.objects.values('category').annotate(count=Count('id')).order_by('-count')

    # Calculate percentage resolved
    resolved = status_counts.get('resolved', 0)
    resolution_rate = round((resolved / total_count * 100), 1) if total_count > 0 else 0.0

    return render(request, 'public/transparency.html', {
        'total_count': total_count,
        'status_counts': status_counts,
        'category_counts': category_counts,
        'resolution_rate': resolution_rate,
        'category_labels': dict(Report.CATEGORY_CHOICES),
    })


def privacy_policy(request):
    """Privacy charter and responsible anonymity disclosure."""
    return render(request, 'public/privacy.html')


def terms_of_service(request):
    """Platform usage terms, legal disclaimer, and malicious filing penalties."""
    return render(request, 'public/terms.html')

