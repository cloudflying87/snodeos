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


class Officer(models.Model):
    name = models.CharField(max_length=100)
    title = models.CharField(max_length=100)
    snowmobile_brand = models.CharField(max_length=50, blank=True)
    photo = models.ImageField(upload_to='officers/', blank=True, null=True)
    email = models.EmailField(blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'name']

    def __str__(self):
        return f'{self.name} — {self.title}'


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
