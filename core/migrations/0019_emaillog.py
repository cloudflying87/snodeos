from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0018_auditlog'),
    ]

    operations = [
        migrations.CreateModel(
            name='EmailLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('subject', models.CharField(max_length=255)),
                ('recipient', models.EmailField(max_length=254)),
                ('template', models.CharField(blank=True, help_text='Template name used to render the email', max_length=80)),
                ('status', models.CharField(choices=[('success', 'Sent'), ('failed', 'Failed')], db_index=True, default='success', max_length=10)),
                ('error', models.TextField(blank=True, help_text='Exception message if status=failed')),
                ('provider', models.CharField(blank=True, help_text='resend / brevo / django', max_length=20)),
                ('sent_at', models.DateTimeField(auto_now_add=True, db_index=True)),
            ],
            options={'ordering': ['-sent_at']},
        ),
    ]
