"""Models for staff investigation reviews, confidential internal notes, and investigation tasks."""

from django.db import models
from django.contrib.auth.models import User
from apps.reports.models import Report

class ReviewNote(models.Model):
    """Confidential internal note written by departmental staff."""

    URGENCY_CHOICES = [
        ('normal', 'Standard Note'),
        ('important', 'Important Detail'),
        ('urgent', 'Urgent Action Required'),
    ]

    report = models.ForeignKey(Report, on_delete=models.CASCADE, related_name='internal_notes')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='review_notes')
    content = models.TextField(help_text="Confidential case notes (staff-only visibility)")
    urgency = models.CharField(max_length=20, choices=URGENCY_CHOICES, default='normal')
    is_pinned = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-is_pinned', '-created_at']

    def __str__(self):
        return f"Note by {self.author.username} on {self.report.reference_id} ({self.created_at})"


class InvestigationTask(models.Model):
    """Actionable checklist item for investigating a case."""

    report = models.ForeignKey(Report, on_delete=models.CASCADE, related_name='tasks')
    title = models.CharField(max_length=255)
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='investigation_tasks')
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    completed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='completed_tasks')
    due_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['is_completed', 'created_at']

    def __str__(self):
        status = "DONE" if self.is_completed else "TODO"
        return f"[{status}] {self.title} ({self.report.reference_id})"
