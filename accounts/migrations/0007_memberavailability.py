import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0006_membergroup'),
    ]

    operations = [
        migrations.CreateModel(
            name='MemberAvailability',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('kind', models.CharField(choices=[
                    ('recurring', 'Recurring weekly'),
                    ('specific',  'Specific date range'),
                ], max_length=10)),
                ('day_of_week', models.PositiveSmallIntegerField(blank=True, choices=[
                    (0, 'Monday'), (1, 'Tuesday'), (2, 'Wednesday'),
                    (3, 'Thursday'), (4, 'Friday'), (5, 'Saturday'), (6, 'Sunday'),
                ], null=True)),
                ('start_time', models.TimeField(blank=True, null=True)),
                ('end_time', models.TimeField(blank=True, null=True)),
                ('starts_at', models.DateTimeField(blank=True, null=True)),
                ('ends_at', models.DateTimeField(blank=True, null=True)),
                ('notes', models.CharField(blank=True, max_length=200)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('member', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,
                                              related_name='availabilities', to=settings.AUTH_USER_MODEL)),
            ],
            options={'ordering': ['kind', 'day_of_week', 'starts_at']},
        ),
    ]
