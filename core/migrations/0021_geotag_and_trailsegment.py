from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0020_inboundsms'),
    ]

    operations = [
        migrations.AddField(
            model_name='announcementimage',
            name='lat',
            field=models.DecimalField(blank=True, db_index=True, decimal_places=6, max_digits=9, null=True),
        ),
        migrations.AddField(
            model_name='announcementimage',
            name='lng',
            field=models.DecimalField(blank=True, db_index=True, decimal_places=6, max_digits=9, null=True),
        ),
        migrations.AddField(
            model_name='trailconditionimage',
            name='lat',
            field=models.DecimalField(blank=True, db_index=True, decimal_places=6, max_digits=9, null=True),
        ),
        migrations.AddField(
            model_name='trailconditionimage',
            name='lng',
            field=models.DecimalField(blank=True, db_index=True, decimal_places=6, max_digits=9, null=True),
        ),
        migrations.AddField(
            model_name='trailworkimage',
            name='lat',
            field=models.DecimalField(blank=True, db_index=True, decimal_places=6, max_digits=9, null=True),
        ),
        migrations.AddField(
            model_name='trailworkimage',
            name='lng',
            field=models.DecimalField(blank=True, db_index=True, decimal_places=6, max_digits=9, null=True),
        ),
        migrations.CreateModel(
            name='TrailSegment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=120)),
                ('description', models.TextField(blank=True)),
                ('status', models.CharField(choices=[
                    ('open', 'Open'),
                    ('closed', 'Closed'),
                    ('caution', 'Use Caution'),
                    ('groomed', 'Recently Groomed'),
                    ('planned', 'Planned / Future'),
                ], db_index=True, default='open', max_length=10)),
                ('difficulty', models.CharField(blank=True, choices=[
                    ('', '— Not set —'),
                    ('easy', 'Easy'),
                    ('moderate', 'Moderate'),
                    ('hard', 'Difficult'),
                ], default='', max_length=10)),
                ('visibility', models.CharField(choices=[
                    ('public', 'Public — shown on the public map'),
                    ('members', 'Members Only — only logged-in members see it'),
                    ('both', 'Both'),
                ], default='both', max_length=10)),
                ('color', models.CharField(blank=True, help_text='Optional hex color override (e.g. #FF6600). Leave blank to color by status.', max_length=7)),
                ('geometry', models.JSONField(default=list, help_text='List of [lat, lng] pairs defining the trail polyline')),
                ('groomed_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={'ordering': ['name']},
        ),
    ]
