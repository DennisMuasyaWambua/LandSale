from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from super_admin.models import AdminRole


class Command(BaseCommand):
    help = 'Creates the unified admin role with combined permissions from content_admin, finance_admin, and support_admin'

    def handle(self, *args, **options):
        self.stdout.write('Creating unified admin role...')

        try:
            # Create admin group
            admin_group, created = Group.objects.get_or_create(name='Admin')
            if created:
                self.stdout.write(self.style.SUCCESS('✓ Created Admin group'))
            else:
                self.stdout.write('Admin group already exists')

            # Get all permissions from content_admin, finance_admin, support_admin
            all_permissions = set()

            try:
                content_admin = AdminRole.objects.get(role_type='content_admin')
                all_permissions.update(content_admin.group.permissions.all())
                self.stdout.write(f'  Added {content_admin.group.permissions.count()} permissions from content_admin')
            except AdminRole.DoesNotExist:
                self.stdout.write(self.style.WARNING('  content_admin role not found, skipping'))

            try:
                finance_admin = AdminRole.objects.get(role_type='finance_admin')
                all_permissions.update(finance_admin.group.permissions.all())
                self.stdout.write(f'  Added {finance_admin.group.permissions.count()} permissions from finance_admin')
            except AdminRole.DoesNotExist:
                self.stdout.write(self.style.WARNING('  finance_admin role not found, skipping'))

            try:
                support_admin = AdminRole.objects.get(role_type='support_admin')
                all_permissions.update(support_admin.group.permissions.all())
                self.stdout.write(f'  Added {support_admin.group.permissions.count()} permissions from support_admin')
            except AdminRole.DoesNotExist:
                self.stdout.write(self.style.WARNING('  support_admin role not found, skipping'))

            # Set permissions on admin group
            admin_group.permissions.set(all_permissions)
            self.stdout.write(f'✓ Set {len(all_permissions)} total permissions on Admin group')

            # Create or update AdminRole
            admin_role, created = AdminRole.objects.update_or_create(
                role_type='admin',
                defaults={
                    'group': admin_group,
                    'description': 'Unified admin role with content, finance, and support privileges',
                    'can_access_dashboard': True,
                    'can_export_data': True,
                    'can_view_audit_logs': True,
                    'api_rate_limit': 5000,
                    'accessible_modules': [
                        'users', 'projects', 'plots', 'bookings', 'sales',
                        'payments', 'subscriptions', 'settings'
                    ]
                }
            )

            if created:
                self.stdout.write(self.style.SUCCESS('✓ Created AdminRole for unified admin'))
            else:
                self.stdout.write(self.style.SUCCESS('✓ Updated existing AdminRole for unified admin'))

            self.stdout.write(self.style.SUCCESS('\nUnified admin role created successfully!'))
            self.stdout.write(f'  Role: {admin_role.role_type}')
            self.stdout.write(f'  Description: {admin_role.description}')
            self.stdout.write(f'  Permissions: {len(all_permissions)}')
            self.stdout.write(f'  Accessible modules: {", ".join(admin_role.accessible_modules)}')

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error creating unified admin role: {str(e)}'))
            raise
