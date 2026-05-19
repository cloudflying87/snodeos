import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0015_trail_condition'),
    ]

    operations = [
        migrations.CreateModel(
            name='AnnouncementImage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.ImageField(upload_to='announcements/')),
                ('caption', models.CharField(blank=True, max_length=200)),
                ('uploaded_at', models.DateTimeField(auto_now_add=True)),
                ('announcement', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='images', to='core.announcement')),
            ],
            options={'ordering': ['uploaded_at']},
        ),
        migrations.CreateModel(
            name='TrailConditionImage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.ImageField(upload_to='trail_conditions/')),
                ('caption', models.CharField(blank=True, max_length=200)),
                ('uploaded_at', models.DateTimeField(auto_now_add=True)),
                ('condition', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='images', to='core.trailcondition')),
            ],
            options={'ordering': ['uploaded_at']},
        ),
    ]
