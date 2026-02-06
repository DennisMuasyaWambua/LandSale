from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from authentication.models import UserSubscription, SubscriptionPlan
from django.utils import timezone
from datetime import timedelta


class Command(BaseCommand):
    help = 'Grant admin privileges and activate subscription for a user'

    def add_arguments(self, parser):
        parser.add_argument('email', type=str, help='User email address')
        parser.add_argument(
            '--no-subscription',
            action='store_true',
            help='Skip subscription activation',
        )

    def handle(self, *args, **options):
        email = options['email']
        skip_subscription = options['no_subscription']

        try:
            user = User.objects.get(email=email)
            self.stdout.write(f"Found user: {user.username} ({user.email})")

            # Grant admin privileges
            user.is_staff = True
            user.is_superuser = True
            user.save()
            self.stdout.write(self.style.SUCCESS(f"✓ Granted admin privileges to {user.email}"))

            if not skip_subscription:
                # Get or create subscription
                subscription, created = UserSubscription.objects.get_or_create(
                    user=user,
                    defaults={
                        'status': 'active',
                        'start_date': timezone.now(),
                        'end_date': timezone.now() + timedelta(days=365),  # 1 year
                        'auto_renew': True,
                    }
                )

                if not created:
                    # Update existing subscription
                    subscription.status = 'active'
                    subscription.start_date = timezone.now()
                    subscription.end_date = timezone.now() + timedelta(days=365)
                    subscription.auto_renew = True
                    subscription.save()
                    self.stdout.write(self.style.SUCCESS(f"✓ Updated subscription for {user.email}"))
                else:
                    self.stdout.write(self.style.SUCCESS(f"✓ Created active subscription for {user.email}"))

                self.stdout.write(f"  Status: {subscription.status}")
                self.stdout.write(f"  Start: {subscription.start_date}")
                self.stdout.write(f"  End: {subscription.end_date}")

            self.stdout.write(self.style.SUCCESS("\n✓ All changes completed successfully!"))

        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"✗ User with email '{email}' not found"))
            return

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"✗ Error: {str(e)}"))
            raise
