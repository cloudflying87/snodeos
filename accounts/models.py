from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models


class RegistrationField(models.Model):
    """Controls which optional fields appear on the public membership application form."""

    CONFIGURABLE_FIELDS = [
        ('phone',            'Phone Number'),
        ('address',          'Street Address'),
        ('city',             'City'),
        ('state',            'State'),
        ('zip_code',         'Zip Code'),
        ('snowmobile_brand', 'Snowmobile Brand / Sled'),
    ]

    field_name  = models.CharField(max_length=50, unique=True, choices=CONFIGURABLE_FIELDS)
    label       = models.CharField(max_length=100, blank=True, help_text='Override the default label (leave blank to use default)')
    is_enabled  = models.BooleanField(default=True,  help_text='Show this field on the registration form')
    is_required = models.BooleanField(default=False, help_text='Make this field required')
    order       = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.get_field_name_display()

    @classmethod
    def enabled_fields(cls):
        return cls.objects.filter(is_enabled=True).order_by('order')


class MemberManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Email is required')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('membership_status', 'active')
        return self.create_user(email, password, **extra_fields)


class Member(AbstractBaseUser, PermissionsMixin):
    SNOWMOBILE_BRANDS = [
        ('polaris', 'Polaris'),
        ('ski-doo', 'Ski-Doo'),
        ('arctic_cat', 'Arctic Cat'),
        ('yamaha', 'Yamaha'),
        ('lynx', 'Lynx'),
        ('other', 'Other'),
    ]

    MEMBERSHIP_STATUS = [
        ('pending', 'Pending Approval'),
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('expired', 'Expired'),
    ]

    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    phone = models.CharField(max_length=20, blank=True)
    address = models.CharField(max_length=200, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=50, blank=True, default='MN')
    zip_code = models.CharField(max_length=10, blank=True)
    snowmobile_brand = models.CharField(max_length=20, choices=SNOWMOBILE_BRANDS, blank=True)
    membership_status = models.CharField(max_length=20, choices=MEMBERSHIP_STATUS, default='pending')
    membership_year = models.PositiveIntegerField(null=True, blank=True)
    is_officer    = models.BooleanField(default=False)
    is_site_admin = models.BooleanField(default=False, help_text='Full access including Communications and Settings')
    officer_title = models.CharField(max_length=100, blank=True)
    photo = models.ImageField(upload_to='member_photos/', blank=True, null=True)
    notes = models.TextField(blank=True)
    date_applied = models.DateTimeField(auto_now_add=True)
    date_approved = models.DateField(null=True, blank=True)

    accepts_texts   = models.BooleanField(null=True, blank=True)  # SMS consent (Yes/No/not answered)
    num_snowmobiles = models.PositiveSmallIntegerField(null=True, blank=True)
    referral_source = models.TextField(blank=True)

    dues_paid      = models.BooleanField(default=False)
    dues_paid_date = models.DateField(null=True, blank=True)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = MemberManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    class Meta:
        ordering = ['last_name', 'first_name']
        verbose_name = 'Member'
        verbose_name_plural = 'Members'

    def __str__(self):
        return f'{self.first_name} {self.last_name}'

    def get_full_name(self):
        return f'{self.first_name} {self.last_name}'

    def get_short_name(self):
        return self.first_name


class MemberGroup(models.Model):
    """A targeted subset of members officers can message together. Used to send
    email blasts and texts to a specific crew (e.g. "Groomers", "Sign Crew")
    without spamming the whole roster."""
    name        = models.CharField(max_length=80, unique=True)
    description = models.CharField(max_length=200, blank=True,
                                   help_text='Short note describing who is in this group')
    members     = models.ManyToManyField('Member', related_name='groups_membership', blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    @property
    def member_count(self):
        return self.members.count()

    @property
    def active_member_count(self):
        return self.members.filter(membership_status='active').count()


class MemberAvailability(models.Model):
    """A member's stated availability — either a recurring weekly window or
    a specific date range. Used to rank candidate volunteers for events."""
    KIND_CHOICES = [
        ('recurring', 'Recurring weekly'),
        ('specific',  'Specific date range'),
    ]
    DAY_CHOICES = [
        (0, 'Monday'), (1, 'Tuesday'), (2, 'Wednesday'),
        (3, 'Thursday'), (4, 'Friday'), (5, 'Saturday'), (6, 'Sunday'),
    ]
    member       = models.ForeignKey('Member', on_delete=models.CASCADE, related_name='availabilities')
    kind         = models.CharField(max_length=10, choices=KIND_CHOICES)
    # For recurring:
    day_of_week  = models.PositiveSmallIntegerField(null=True, blank=True, choices=DAY_CHOICES)
    start_time   = models.TimeField(null=True, blank=True)
    end_time     = models.TimeField(null=True, blank=True)
    # For specific:
    starts_at    = models.DateTimeField(null=True, blank=True)
    ends_at      = models.DateTimeField(null=True, blank=True)
    notes        = models.CharField(max_length=200, blank=True)
    created_at   = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['kind', 'day_of_week', 'starts_at']

    def __str__(self):
        if self.kind == 'recurring':
            return f'{self.member.get_short_name()}: {self.get_day_of_week_display()} {self.start_time}-{self.end_time}'
        return f'{self.member.get_short_name()}: {self.starts_at} – {self.ends_at}'

    def covers(self, start_dt, end_dt):
        """Does this availability fully cover the given UTC datetime range?"""
        if self.kind == 'specific':
            if not (self.starts_at and self.ends_at):
                return False
            return self.starts_at <= start_dt and self.ends_at >= end_dt

        # Recurring — same calendar day, day-of-week matches, time window covers
        if self.day_of_week is None or self.start_time is None or self.end_time is None:
            return False
        if start_dt.date() != end_dt.date():
            return False  # multi-day events: skip recurring match for v1
        if start_dt.weekday() != self.day_of_week:
            return False
        return self.start_time <= start_dt.time() and self.end_time >= end_dt.time()

    @property
    def display(self):
        if self.kind == 'recurring':
            return f'{self.get_day_of_week_display()}s, {self.start_time:%-I:%M %p} – {self.end_time:%-I:%M %p}'
        return f'{self.starts_at:%a %b %-d, %-I:%M %p} – {self.ends_at:%-I:%M %p}'
