from django.db import models


class ClubStats(models.Model):
    members_count = models.PositiveIntegerField(default=0)
    miles_maintained = models.PositiveIntegerField(default=0)
    annual_budget = models.PositiveIntegerField(default=0)
    supporting_landowners = models.PositiveIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Club Stats'
        verbose_name_plural = 'Club Stats'

    def __str__(self):
        return f'Club Stats (updated {self.updated_at:%Y-%m-%d})'


class OfficerTitle(models.Model):
    name  = models.CharField(max_length=100, unique=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'name']

    def __str__(self):
        return self.name


class Officer(models.Model):
    name             = models.CharField(max_length=100)
    title            = models.CharField(max_length=100)
    snowmobile_brand = models.CharField(max_length=50, blank=True)
    photo            = models.ImageField(upload_to='officers/', blank=True, null=True)
    email            = models.EmailField(blank=True)
    phone            = models.CharField(max_length=20, blank=True)
    order            = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'name']

    def __str__(self):
        return f'{self.name} — {self.title}'

    @property
    def is_director(self):
        return self.title == 'Director'


class Sponsor(models.Model):
    name = models.CharField(max_length=100)
    website = models.URLField(blank=True)
    logo = models.ImageField(upload_to='sponsors/', blank=True, null=True)
    description = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['order', 'name']

    def __str__(self):
        return self.name


class TrailWorkLog(models.Model):
    date = models.DateField()
    title = models.CharField(max_length=200)
    description = models.TextField()
    volunteers = models.PositiveIntegerField(default=0)
    hours = models.DecimalField(max_digits=6, decimal_places=1, default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f'{self.date} — {self.title}'


class TrailWorkImage(models.Model):
    log = models.ForeignKey(TrailWorkLog, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='trail_work/')
    caption = models.CharField(max_length=200, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['uploaded_at']

    def __str__(self):
        return f'Image for {self.log}'


class Announcement(models.Model):
    VISIBILITY_CHOICES = [
        ('members', 'Members Only — shown on member dashboard'),
        ('public',  'Public — shown on home page & triggers Zapier'),
        ('both',    'Both — home page, member dashboard & Zapier'),
    ]

    title      = models.CharField(max_length=200)
    body       = models.TextField()
    visibility = models.CharField(max_length=10, choices=VISIBILITY_CHOICES, default='members')
    is_pinned  = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-is_pinned', '-created_at']

    def __str__(self):
        return self.title

    @property
    def is_public(self):
        return self.visibility in ('public', 'both')

    @property
    def is_member_visible(self):
        return self.visibility in ('members', 'both')


class EmailTemplate(models.Model):
    """Reusable branded email templates officers can select when composing blasts."""
    name             = models.CharField(max_length=100, unique=True)
    description      = models.CharField(max_length=200, blank=True, help_text='Short description shown in the selector')
    from_name        = models.CharField(max_length=100, default='Brainerd Snodeos')
    header_color     = models.CharField(max_length=7, default='#1363A2')
    accent_color     = models.CharField(max_length=7, default='#1363A2')
    header_image     = models.ImageField(upload_to='email_headers/', blank=True, null=True)
    footer_text      = models.TextField(blank=True, default="You're receiving this as a member of the Brainerd Snodeos Snowmobile Club.")
    is_default       = models.BooleanField(default=False, help_text='Default template used when none is specified')
    created_at       = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-is_default', 'name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        # Only one template can be default at a time
        if self.is_default:
            EmailTemplate.objects.exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)

    @property
    def header_image_url(self):
        """Absolute URL for use in emails (requires SITE_URL in settings)."""
        if not self.header_image:
            return ''
        from django.conf import settings as _settings
        site_url = getattr(_settings, 'SITE_URL', '').rstrip('/')
        return f"{site_url}{self.header_image.url}"

    @classmethod
    def get_default(cls):
        return cls.objects.filter(is_default=True).first() or cls.objects.first()


class SiteSettings(models.Model):
    FACEBOOK_CHOICES = [
        ('none',   'Disabled'),
        ('plugin', 'Page Plugin (embed feed on site — requires App ID)'),
        ('zapier', 'Zapier Auto-Post (auto-post announcements to Facebook)'),
    ]
    facebook_integration = models.CharField(max_length=20, choices=FACEBOOK_CHOICES, default='none')
    facebook_page_url    = models.URLField(blank=True, default='https://www.facebook.com/brainerdsnodeos')
    facebook_app_id      = models.CharField(max_length=50, blank=True)
    zapier_webhook_url   = models.URLField(blank=True)

    # Communications — email
    brevo_smtp_key    = models.CharField(max_length=200, blank=True)
    resend_api_key    = models.CharField(max_length=200, blank=True)
    notification_email = models.EmailField(blank=True, help_text='Where officer alerts go (new applications, contact messages)')

    # Email branding
    email_from_name   = models.CharField(max_length=100, blank=True, default='Brainerd Snodeos')
    email_header_color = models.CharField(max_length=7, blank=True, default='#1363A2', help_text='Hex color for the email header bar')
    email_accent_color = models.CharField(max_length=7, blank=True, default='#1363A2', help_text='Hex color for buttons and accents')
    email_footer_text  = models.TextField(blank=True, default="You're receiving this because you're a member of the Brainerd Snodeos Snowmobile Club.")

    # Communications — SMS
    brevo_api_key      = models.CharField(max_length=200, blank=True)
    twilio_account_sid = models.CharField(max_length=50, blank=True)
    twilio_auth_token  = models.CharField(max_length=50, blank=True)
    twilio_from_number = models.CharField(max_length=20, blank=True)

    # Per-email-type template assignments
    template_contact_reply = models.ForeignKey(
        'EmailTemplate', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='+',
        help_text='Template for auto-replies to contact form submitters',
    )
    template_member = models.ForeignKey(
        'EmailTemplate', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='+',
        help_text='Template for member-facing transactional emails (application approved, etc.)',
    )
    template_announcement = models.ForeignKey(
        'EmailTemplate', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='+',
        help_text='Template for announcement email blasts',
    )

    class Meta:
        verbose_name = 'Site Settings'

    @classmethod
    def get(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def __str__(self):
        return 'Site Settings'

    # ── Helpers ──────────────────────────────────────────────────────────────
    @property
    def email_configured(self):
        return bool(self.brevo_smtp_key or self.resend_api_key)

    @property
    def sms_configured(self):
        return bool(self.brevo_api_key or self.twilio_account_sid)

    class Meta:
        verbose_name = 'Site Settings'

    @classmethod
    def get(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def __str__(self):
        return 'Site Settings'


class ContactMessage(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    subject = models.CharField(max_length=200)
    message = models.TextField()
    submitted_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['-submitted_at']

    def __str__(self):
        return f'{self.name} — {self.subject}'
