from django.core.management.base import BaseCommand
from authentication.models import PasswordReset
from django.utils import timezone


class Command(BaseCommand):
    help = 'Show active password reset tokens (for development/testing only)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            type=str,
            help='Filter by user email',
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Show all tokens including expired and used',
        )

    def handle(self, *args, **options):
        email = options.get('email')
        show_all = options.get('all')

        queryset = PasswordReset.objects.select_related('user').all()

        if email:
            queryset = queryset.filter(user__email=email)

        if not show_all:
            queryset = queryset.filter(
                is_used=False,
                expires_at__gt=timezone.now()
            )

        queryset = queryset.order_by('-created_at')

        if not queryset.exists():
            self.stdout.write(self.style.WARNING('No password reset tokens found.'))
            return

        self.stdout.write(self.style.SUCCESS(f'\nFound {queryset.count()} password reset token(s):\n'))

        for reset in queryset:
            status = []
            if reset.is_used:
                status.append(self.style.ERROR('USED'))
            elif not reset.is_valid():
                status.append(self.style.ERROR('EXPIRED'))
            else:
                status.append(self.style.SUCCESS('VALID'))

            time_left = (reset.expires_at - timezone.now()).total_seconds() / 60
            time_info = f"{int(time_left)} minutes" if time_left > 0 else "expired"

            self.stdout.write(
                f"\nEmail: {reset.user.email}\n"
                f"Token: {reset.token}\n"
                f"Status: {' '.join(status)}\n"
                f"Created: {reset.created_at.strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"Expires: {reset.expires_at.strftime('%Y-%m-%d %H:%M:%S')} ({time_info})\n"
                f"Reset URL: http://localhost:3000/reset-password?token={reset.token}\n"
                f"{'-' * 70}"
            )

        self.stdout.write(self.style.SUCCESS(f'\n\nTotal: {queryset.count()} token(s)\n'))
