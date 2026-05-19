from django.contrib import admin
from .models import ClubStats, Officer, Sponsor, TrailWorkLog, ContactMessage, Announcement


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ('title', 'is_pinned', 'created_at')
    list_editable = ('is_pinned',)


@admin.register(ClubStats)
class ClubStatsAdmin(admin.ModelAdmin):
    list_display = ('members_count', 'miles_maintained', 'annual_budget', 'supporting_landowners', 'updated_at')


@admin.register(Officer)
class OfficerAdmin(admin.ModelAdmin):
    list_display = ('name', 'title', 'snowmobile_brand', 'order')
    list_editable = ('order',)


@admin.register(Sponsor)
class SponsorAdmin(admin.ModelAdmin):
    list_display = ('name', 'website', 'is_active', 'order')
    list_editable = ('is_active', 'order')


@admin.register(TrailWorkLog)
class TrailWorkLogAdmin(admin.ModelAdmin):
    list_display = ('date', 'title', 'volunteers', 'hours')


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'subject', 'submitted_at', 'is_read')
    list_filter = ('is_read',)
    list_editable = ('is_read',)
