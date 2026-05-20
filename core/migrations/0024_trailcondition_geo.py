from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0023_events_equipment'),
    ]

    operations = [
        migrations.AddField(
            model_name='trailcondition',
            name='lat',
            field=models.DecimalField(
                blank=True, db_index=True, decimal_places=6, max_digits=9, null=True,
                help_text='Optional location pin (auto-filled when created by clicking the map)',
            ),
        ),
        migrations.AddField(
            model_name='trailcondition',
            name='lng',
            field=models.DecimalField(
                blank=True, db_index=True, decimal_places=6, max_digits=9, null=True,
            ),
        ),
    ]
