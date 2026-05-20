from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0025_messaging_notifications_shares_recurrence'),
    ]

    operations = [
        migrations.AlterField(
            model_name='auditlog',
            name='action',
            field=models.CharField(choices=[
                ('member_approve', 'Approved member'),
                ('member_deactivate', 'Deactivated member'),
                ('member_delete', 'Deleted member'),
                ('email_blast', 'Sent email blast'),
                ('sms_blast', 'Sent text blast'),
                ('message_sent', 'Sent inbox message'),
                ('announcement_send', 'Sent announcement notification'),
                ('trail_condition_send', 'Sent trail condition notification'),
                ('photo_approve', 'Approved member photo'),
                ('photo_reject', 'Rejected member photo'),
                ('settings_change', 'Changed settings'),
            ], max_length=40),
        ),
    ]
