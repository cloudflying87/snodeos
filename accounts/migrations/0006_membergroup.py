from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0005_member_site_admin'),
    ]

    operations = [
        migrations.CreateModel(
            name='MemberGroup',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=80, unique=True)),
                ('description', models.CharField(blank=True, help_text='Short note describing who is in this group', max_length=200)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('members', models.ManyToManyField(blank=True, related_name='groups_membership', to=settings.AUTH_USER_MODEL)),
            ],
            options={'ordering': ['name']},
        ),
    ]
