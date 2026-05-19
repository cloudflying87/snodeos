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
