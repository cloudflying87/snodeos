import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0024_trailcondition_geo'),
    ]

    operations = [
        # Trail FKs on TrailCondition and TrailWorkLog
        migrations.AddField(
            model_name='trailcondition',
            name='trail',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='conditions', to='core.trailsegment',
                help_text='Which trail this condition applies to (optional)',
            ),
        ),
        migrations.AddField(
            model_name='trailworklog',
            name='trail',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='work_logs', to='core.trailsegment',
                help_text='Which trail this work happened on (optional)',
            ),
        ),
        # Event recurrence fields
        migrations.AddField(
            model_name='event',
            name='recurrence',
            field=models.CharField(choices=[
                ('none', 'No repeat'),
                ('daily', 'Daily'),
                ('weekly', 'Weekly'),
                ('biweekly', 'Every two weeks'),
                ('monthly', 'Monthly'),
            ], default='none', max_length=10),
        ),
        migrations.AddField(
            model_name='event',
            name='recurrence_count',
            field=models.PositiveIntegerField(blank=True, help_text='How many occurrences total (incl. the first)', null=True),
        ),
        migrations.AddField(
            model_name='event',
            name='recurrence_group',
            field=models.UUIDField(blank=True, db_index=True, help_text='Shared between all occurrences expanded from one recurring event', null=True),
        ),
        # Internal messaging
        migrations.CreateModel(
            name='Conversation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('subject', models.CharField(max_length=200)),
                ('last_activity', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('participants', models.ManyToManyField(related_name='conversations', to=settings.AUTH_USER_MODEL)),
            ],
            options={'ordering': ['-last_activity']},
        ),
        migrations.CreateModel(
            name='InternalMessage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('body', models.TextField()),
                ('sent_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('conversation', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='messages', to='core.conversation')),
                ('sender', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='sent_messages', to=settings.AUTH_USER_MODEL)),
                ('read_by', models.ManyToManyField(blank=True, related_name='read_messages', to=settings.AUTH_USER_MODEL)),
            ],
            options={'ordering': ['sent_at']},
        ),
        # Notifications
        migrations.CreateModel(
            name='Notification',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('kind', models.CharField(choices=[
                    ('message', 'New message'),
                    ('event_assigned', 'Added to an event'),
                    ('event_signup', 'Someone signed up for your event'),
                    ('photo_submission', 'New photo to review'),
                    ('application', 'New membership application'),
                    ('other', 'Other'),
                ], max_length=20)),
                ('title', models.CharField(max_length=200)),
                ('url', models.CharField(blank=True, help_text='Where to send the user when they click the notification', max_length=300)),
                ('is_read', models.BooleanField(db_index=True, default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='notifications', to=settings.AUTH_USER_MODEL)),
            ],
            options={'ordering': ['-created_at']},
        ),
        # Member photo submissions
        migrations.CreateModel(
            name='MemberShare',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.ImageField(upload_to='member_shares/')),
                ('caption', models.CharField(blank=True, max_length=300)),
                ('lat', models.DecimalField(blank=True, db_index=True, decimal_places=6, max_digits=9, null=True)),
                ('lng', models.DecimalField(blank=True, db_index=True, decimal_places=6, max_digits=9, null=True)),
                ('status', models.CharField(choices=[
                    ('pending', 'Pending Review'),
                    ('approved', 'Approved'),
                    ('rejected', 'Rejected'),
                ], db_index=True, default='pending', max_length=10)),
                ('reviewed_at', models.DateTimeField(blank=True, null=True)),
                ('review_note', models.CharField(blank=True, max_length=300)),
                ('submitted_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('member', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='photo_shares', to=settings.AUTH_USER_MODEL)),
                ('reviewed_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='reviewed_shares', to=settings.AUTH_USER_MODEL)),
            ],
            options={'ordering': ['-submitted_at']},
        ),
    ]
