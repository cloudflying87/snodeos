import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0017_sitesettings_social'),
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='AuditLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('action', models.CharField(choices=[
                    ('member_approve', 'Approved member'),
                    ('member_deactivate', 'Deactivated member'),
                    ('member_delete', 'Deleted member'),
                    ('email_blast', 'Sent email blast'),
                    ('sms_blast', 'Sent text blast'),
                    ('announcement_send', 'Sent announcement notification'),
                    ('trail_condition_send', 'Sent trail condition notification'),
                    ('settings_change', 'Changed settings'),
                ], max_length=40)),
                ('target', models.CharField(blank=True, help_text='What was acted on (member name, blast subject, etc.)', max_length=200)),
                ('detail', models.TextField(blank=True, help_text='Additional context (recipient count, etc.)')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('actor', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='audit_actions',
                    to=settings.AUTH_USER_MODEL,
                    help_text='Officer who performed the action',
                )),
            ],
            options={'ordering': ['-created_at']},
        ),
    ]
