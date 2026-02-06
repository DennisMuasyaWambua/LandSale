#!/usr/bin/env python
"""
Script to grant admin privileges and activate subscription for a user
Connects directly to production database
"""
import os
import sys
import django
from datetime import timedelta
from django.utils import timezone

# Set up Django with production database
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'land_sale.settings')

# Override database settings to use production
os.environ['DATABASE_URL'] = 'postgresql://postgres:hkUcYuRgxfNvOtGfpOsycbaCECenpyNu@ballast.proxy.rlwy.net:23763/railway'

# Update settings before Django setup
from django.conf import settings
settings.DATABASES['default'] = {
    'ENGINE': 'django.db.backends.postgresql',
    'NAME': 'railway',
    'USER': 'postgres',
    'PASSWORD': 'hkUcYuRgxfNvOtGfpOsycbaCECenpyNu',
    'HOST': 'ballast.proxy.rlwy.net',
    'PORT': '23763',
}

django.setup()

from django.contrib.auth.models import User
from authentication.models import UserSubscription

def grant_admin_privileges(email):
    """Grant admin privileges and activate subscription"""
    try:
        # Find user
        user = User.objects.get(email=email)
        print(f"✓ Found user: {user.username} ({user.email})")
        print(f"  ID: {user.id}")
        print(f"  Current admin status: is_staff={user.is_staff}, is_superuser={user.is_superuser}")

        # Grant admin privileges
        user.is_staff = True
        user.is_superuser = True
        user.save()
        print(f"\n✓ Granted admin privileges")
        print(f"  is_staff: {user.is_staff}")
        print(f"  is_superuser: {user.is_superuser}")

        # Handle subscription
        try:
            subscription = UserSubscription.objects.get(user=user)
            print(f"\n✓ Found existing subscription")
            print(f"  Current status: {subscription.status}")

            # Update subscription
            subscription.status = 'active'
            subscription.start_date = timezone.now()
            subscription.end_date = timezone.now() + timedelta(days=365)
            subscription.auto_renew = True
            subscription.save()
            print(f"✓ Updated subscription to active")

        except UserSubscription.DoesNotExist:
            # Create new subscription
            subscription = UserSubscription.objects.create(
                user=user,
                status='active',
                start_date=timezone.now(),
                end_date=timezone.now() + timedelta(days=365),
                auto_renew=True,
            )
            print(f"\n✓ Created new active subscription")

        print(f"\nSubscription details:")
        print(f"  Status: {subscription.status}")
        print(f"  Start: {subscription.start_date}")
        print(f"  End: {subscription.end_date}")
        print(f"  Auto-renew: {subscription.auto_renew}")
        print(f"  Is currently active: {subscription.is_active()}")

        print(f"\n✅ All changes completed successfully for {email}!")

    except User.DoesNotExist:
        print(f"❌ Error: User with email '{email}' not found in database")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    email = 'o0sdu7y8l7@bltiwd.com'
    print(f"Connecting to production database...")
    print(f"Processing user: {email}\n")
    grant_admin_privileges(email)
