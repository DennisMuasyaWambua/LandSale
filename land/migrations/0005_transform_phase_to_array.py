from django.db import migrations, models
from django.contrib.postgres.fields import ArrayField


def convert_phase_to_array(apps, schema_editor):
    Project = apps.get_model('land', 'Project')
    for project in Project.objects.all():
        if project.phase and isinstance(project.phase, str):
            project.phase = [project.phase]
            project.save()


def reverse_phase_to_string(apps, schema_editor):
    Project = apps.get_model('land', 'Project')
    for project in Project.objects.all():
        if project.phase and isinstance(project.phase, list) and len(project.phase) > 0:
            project.phase = project.phase[0]
            project.save()


class Migration(migrations.Migration):

    dependencies = [
        ('land', '0004_alter_project_project_svg_map'),
    ]

    operations = [
        # First, remove the fields we don't need
        migrations.RemoveField(
            model_name='project',
            name='price',
        ),
        migrations.RemoveField(
            model_name='project',
            name='property_type',
        ),
        
        # Add temporary array field
        migrations.AddField(
            model_name='project',
            name='phase_array',
            field=ArrayField(models.CharField(max_length=100), blank=True, default=list),
        ),
        
        # Convert existing phase data to array format
        migrations.RunPython(convert_phase_to_array, reverse_phase_to_string),
        
        # Remove old phase field
        migrations.RemoveField(
            model_name='project',
            name='phase',
        ),
        
        # Rename the array field to phase
        migrations.RenameField(
            model_name='project',
            old_name='phase_array',
            new_name='phase',
        ),
    ]