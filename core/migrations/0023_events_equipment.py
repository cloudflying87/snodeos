import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0022_map_defaults'),
        ('accounts', '0007_memberavailability'),
    ]

    operations = [
        migrations.CreateModel(
            name='EquipmentItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=80)),
                ('description', models.TextField(blank=True)),
                ('photo', models.ImageField(blank=True, null=True, upload_to='equipment/')),
                ('is_active', models.BooleanField(default=True)),
            ],
            options={'ordering': ['name']},
        ),
        migrations.CreateModel(
            name='Event',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=180)),
                ('kind', models.CharField(choices=[
                    ('grooming', 'Grooming Run'),
                    ('work', 'Trail Work / Work Party'),
                    ('meeting', 'Meeting'),
                    ('equipment', 'Equipment Use'),
                    ('event', 'Club Event'),
                    ('other', 'Other'),
                ], db_index=True, default='work', max_length=12)),
                ('description', models.TextField(blank=True)),
                ('starts_at', models.DateTimeField(db_index=True)),
                ('ends_at', models.DateTimeField()),
                ('location_text', models.CharField(blank=True, help_text='e.g. "Parking lot off Hwy 25" — used when no trail is linked', max_length=200)),
                ('location_lat', models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True)),
                ('location_lng', models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True)),
                ('status', models.CharField(choices=[
                    ('open', 'Open — needs volunteers'),
                    ('assigned', 'Assigned / scheduled'),
                    ('in_progress', 'In progress'),
                    ('done', 'Completed'),
                    ('cancelled', 'Cancelled'),
                ], db_index=True, default='open', max_length=12)),
                ('visibility', models.CharField(choices=[
                    ('public', 'Public — anyone can see'),
                    ('members', 'Members Only'),
                    ('both', 'Both'),
                ], default='members', max_length=10)),
                ('max_volunteers', models.PositiveIntegerField(blank=True, help_text='Leave blank for unlimited', null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('assignees', models.ManyToManyField(blank=True, related_name='events_assigned', to=settings.AUTH_USER_MODEL)),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL,
                                                  related_name='events_created', to=settings.AUTH_USER_MODEL)),
                ('equipment', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                                                 related_name='events', to='core.equipmentitem')),
                ('location_trail', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                                                      related_name='events', to='core.trailsegment')),
                ('target_group', models.ForeignKey(blank=True, help_text='If set, "Suggested volunteers" prioritizes this group',
                                                    null=True, on_delete=django.db.models.deletion.SET_NULL,
                                                    related_name='events', to='accounts.membergroup')),
            ],
            options={'ordering': ['starts_at']},
        ),
    ]
