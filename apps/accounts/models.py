"""Models for user accounts and citizen reporter profiles."""

from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class ReporterProfile(models.Model):
    """Extended profile for citizens filing reports with redFlag."""

    TRUST_CHOICES = [
        ('standard', 'Standard Reporter'),
        ('verified', 'Verified Citizen (ID Verified)'),
        ('trusted', 'Trusted Civic Partner'),
        ('restricted', 'Flagged / Restricted for Abuse'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone = models.CharField(max_length=30, blank=True)
    address = models.CharField(max_length=255, blank=True)
    trust_status = models.CharField(max_length=20, choices=TRUST_CHOICES, default='standard')
    verification_notes = models.TextField(blank=True, help_text="Departmental notes on citizen verification or credibility")
    reputation_score = models.PositiveIntegerField(default=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Profile of {self.user.username} ({self.get_trust_status_display()})"

    @property
    def total_reports_count(self):
        return self.user.reports.count()

    @property
    def resolved_reports_count(self):
        return self.user.reports.filter(status='resolved').count()

    def get_trust_badge_classes(self):
        mapping = {
            'verified': 'bg-emerald-100 text-emerald-900 border-emerald-300 font-semibold',
            'standard': 'bg-slate-100 text-slate-800 border-slate-300',
            'restricted': 'bg-red-100 text-red-900 border-red-300 font-bold',
        }
        return mapping.get(self.trust_status, 'bg-slate-100 text-slate-800 border-slate-300')


@receiver(post_save, sender=User)
def create_or_save_user_profile(sender, instance, created, **kwargs):
    if created:
        ReporterProfile.objects.create(user=instance)
    else:
        if hasattr(instance, 'profile'):
            instance.profile.save()
        else:
            ReporterProfile.objects.create(user=instance)
