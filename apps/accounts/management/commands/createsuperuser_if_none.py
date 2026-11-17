"""Management command to guarantee only admin1 and admin2 superadmins exist with password 'admin'."""

import os
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

class Command(BaseCommand):
    help = 'Idempotently configure exactly 2 superadmins (admin1 and admin2) with password "admin"'

    def handle(self, *args, **options):
        User = get_user_model()

        superadmins_data = [
            ('admin1', 'admin1@redflag.gov.in', 'Vikram', 'Rathore'),
            ('admin2', 'admin2@redflag.gov.in', 'Ananya', 'Deshmukh'),
        ]

        # 1. Ensure admin1 and admin2 exist with password "admin" and is_superuser=True
        for username, email, first, last in superadmins_data:
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': email,
                    'first_name': first,
                    'last_name': last,
                    'is_staff': True,
                    'is_superuser': True,
                }
            )
            user.set_password('admin')
            user.is_staff = True
            user.is_superuser = True
            user.first_name = first
            user.last_name = last
            user.email = email
            user.save()
            action = "Created" if created else "Updated"
            self.stdout.write(self.style.SUCCESS(f'{action} superadmin "{username}" (Password: "admin").'))

        # 2. Demote any other users who have is_superuser=True so ONLY admin1 and admin2 are superadmins
        demoted_count = User.objects.filter(is_superuser=True).exclude(username__in=['admin1', 'admin2']).update(is_superuser=False)
        if demoted_count > 0:
            self.stdout.write(self.style.WARNING(f'Demoted {demoted_count} non-approved superusers to maintain strictly 2 superadmins.'))

        self.stdout.write(self.style.SUCCESS('Superadmin calibration complete: exactly 2 superadmins active (admin1, admin2).'))
