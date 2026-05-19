from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Member


@admin.register(Member)
class MemberAdmin(UserAdmin):
    model = Member
    list_display = ('email', 'first_name', 'last_name', 'membership_status', 'is_officer', 'is_staff')
    list_filter = ('membership_status', 'is_officer', 'is_staff', 'snowmobile_brand')
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('last_name', 'first_name')

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'phone', 'photo')}),
        ('Address', {'fields': ('address', 'city', 'state', 'zip_code')}),
        ('Club Info', {'fields': ('snowmobile_brand', 'membership_status', 'membership_year', 'is_officer', 'officer_title', 'date_approved', 'notes')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'password1', 'password2', 'membership_status'),
        }),
    )
