from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0021_geotag_and_trailsegment'),
    ]

    operations = [
        migrations.AddField(
            model_name='sitesettings',
            name='map_default_lat',
            field=models.DecimalField(
                decimal_places=6, default=46.358000, max_digits=9,
                help_text='Latitude the map centers on before user data loads. Default: Brainerd, MN.',
            ),
        ),
        migrations.AddField(
            model_name='sitesettings',
            name='map_default_lng',
            field=models.DecimalField(
                decimal_places=6, default=-94.201000, max_digits=9,
                help_text='Longitude the map centers on. Default: Brainerd, MN.',
            ),
        ),
        migrations.AddField(
            model_name='sitesettings',
            name='map_default_zoom',
            field=models.PositiveSmallIntegerField(
                default=11,
                help_text='Default zoom level (1 = world, 19 = street). 11 is good for a county-sized area.',
            ),
        ),
    ]
