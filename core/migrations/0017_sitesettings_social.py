from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0016_announcement_trail_condition_images'),
    ]

    operations = [
        migrations.AddField(
            model_name='sitesettings',
            name='site_description',
            field=models.CharField(
                blank=True,
                default='Brainerd Lakes Area snowmobile club — trail conditions, club events, membership, and trail work.',
                help_text='Shown in link previews when someone shares the site on Facebook, iMessage, etc.',
                max_length=300,
            ),
        ),
        migrations.AddField(
            model_name='sitesettings',
            name='social_image',
            field=models.ImageField(
                blank=True,
                help_text='Square or 1200×630 image used when the site is shared on Facebook, Twitter, iMessage, Slack, etc.',
                null=True,
                upload_to='social/',
            ),
        ),
    ]
