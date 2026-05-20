from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0019_emaillog'),
    ]

    operations = [
        migrations.CreateModel(
            name='InboundSMS',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('from_number', models.CharField(db_index=True, max_length=20)),
                ('body', models.TextField()),
                ('twilio_message_sid', models.CharField(blank=True, help_text='Twilio MessageSid; prevents duplicate webhook calls from inserting twice', max_length=64, unique=True)),
                ('received_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('is_read', models.BooleanField(default=False)),
            ],
            options={'ordering': ['-received_at']},
        ),
    ]
