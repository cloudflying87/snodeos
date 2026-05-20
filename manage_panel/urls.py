from django.urls import path
from . import views

app_name = 'manage_panel'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),

    path('stats/', views.stats_edit, name='stats_edit'),

    path('officers/titles/', views.officer_title_list, name='officer_title_list'),
    path('officers/titles/<int:pk>/delete/', views.officer_title_delete, name='officer_title_delete'),
    path('officers/', views.officer_list, name='officer_list'),
    path('officers/add/', views.officer_add, name='officer_add'),
    path('officers/<int:pk>/edit/', views.officer_edit, name='officer_edit'),
    path('officers/<int:pk>/delete/', views.officer_delete, name='officer_delete'),
    path('officers/reorder/', views.officer_reorder, name='officer_reorder'),

    path('sponsors/', views.sponsor_list, name='sponsor_list'),
    path('sponsors/add/', views.sponsor_add, name='sponsor_add'),
    path('sponsors/<int:pk>/edit/', views.sponsor_edit, name='sponsor_edit'),
    path('sponsors/<int:pk>/delete/', views.sponsor_delete, name='sponsor_delete'),
    path('sponsors/<int:pk>/toggle/', views.sponsor_toggle, name='sponsor_toggle'),

    path('announcements/', views.announcement_list, name='announcement_list'),
    path('announcements/add/', views.announcement_add, name='announcement_add'),
    path('announcements/<int:pk>/edit/', views.announcement_edit, name='announcement_edit'),
    path('announcements/<int:pk>/delete/', views.announcement_delete, name='announcement_delete'),
    path('announcements/<int:pk>/pin/', views.announcement_pin, name='announcement_pin'),
    path('announcements/image/<int:pk>/delete/', views.announcement_image_delete, name='announcement_image_delete'),

    path('trail-conditions/', views.trail_condition_list, name='trail_condition_list'),
    path('trail-conditions/add/', views.trail_condition_add, name='trail_condition_add'),
    path('trail-conditions/<int:pk>/edit/', views.trail_condition_edit, name='trail_condition_edit'),
    path('trail-conditions/<int:pk>/delete/', views.trail_condition_delete, name='trail_condition_delete'),
    path('trail-conditions/<int:pk>/pin/', views.trail_condition_pin, name='trail_condition_pin'),
    path('trail-conditions/image/<int:pk>/delete/', views.trail_condition_image_delete, name='trail_condition_image_delete'),

    path('trail-segments/', views.trail_segment_list, name='trail_segment_list'),
    path('trail-segments/new/', views.trail_segment_editor, name='trail_segment_add'),
    path('trail-segments/<int:pk>/edit/', views.trail_segment_editor, name='trail_segment_edit'),
    path('trail-segments/<int:pk>/delete/', views.trail_segment_delete, name='trail_segment_delete'),

    path('equipment/', views.equipment_list, name='equipment_list'),
    path('equipment/new/', views.equipment_form, name='equipment_add'),
    path('equipment/<int:pk>/edit/', views.equipment_form, name='equipment_edit'),
    path('equipment/<int:pk>/delete/', views.equipment_delete, name='equipment_delete'),

    path('events/', views.event_list, name='event_list'),
    path('events/new/', views.event_form, name='event_add'),
    path('events/<int:pk>/edit/', views.event_form, name='event_edit'),
    path('events/<int:pk>/delete/', views.event_delete, name='event_delete'),
    path('events/<int:pk>/assign/', views.event_assign, name='event_assign'),
    path('events/<int:pk>/unassign/<int:member_pk>/', views.event_unassign, name='event_unassign'),

    path('photo-queue/', views.photo_queue, name='photo_queue'),
    path('photo-queue/<int:pk>/review/', views.photo_review, name='photo_review'),
    path('photo-queue/<int:pk>/delete/', views.photo_delete, name='photo_delete'),

    path('trail-work/', views.trail_work_list, name='trail_work_list'),
    path('trail-work/add/', views.trail_work_add, name='trail_work_add'),
    path('trail-work/<int:pk>/edit/', views.trail_work_edit, name='trail_work_edit'),
    path('trail-work/<int:pk>/delete/', views.trail_work_delete, name='trail_work_delete'),
    path('trail-work/image/<int:pk>/delete/', views.trail_work_image_delete, name='trail_work_image_delete'),

    path('members/import/', views.member_import, name='member_import'),
    path('member-groups/', views.member_group_list, name='member_group_list'),
    path('member-groups/new/', views.member_group_form, name='member_group_add'),
    path('member-groups/<int:pk>/edit/', views.member_group_form, name='member_group_edit'),
    path('member-groups/<int:pk>/delete/', views.member_group_delete, name='member_group_delete'),

    path('messages/', views.message_list, name='message_list'),
    path('messages/<int:pk>/', views.message_detail, name='message_detail'),
    path('messages/<int:pk>/delete/', views.message_delete, name='message_delete'),

    path('registration-form/', views.registration_form_settings, name='registration_form_settings'),
    path('dues/', views.dues, name='dues'),
    path('permissions/', views.permissions, name='permissions'),
    path('facebook/', views.facebook_settings, name='facebook_settings'),
    path('email/', views.email_settings, name='email_settings'),
    path('email/blast/', views.email_blast, name='email_blast'),

    path('communications/', views.communications, name='communications'),
    path('email-templates/', views.email_template_list, name='email_template_list'),
    path('email-templates/add/', views.email_template_add, name='email_template_add'),
    path('email-templates/<int:pk>/edit/', views.email_template_edit, name='email_template_edit'),
    path('email-templates/<int:pk>/delete/', views.email_template_delete, name='email_template_delete'),
    path('email-templates/<int:pk>/api/', views.email_template_api, name='email_template_api'),
    path('email-templates/<int:pk>/test/', views.email_template_test, name='email_template_test'),
    path('setup-guide/', views.setup_guide, name='setup_guide'),
    path('audit-log/', views.audit_log, name='audit_log'),
    path('email-log/', views.email_log, name='email_log'),
    path('text-members/', views.text_members, name='text_members'),
    path('sms-settings/', views.sms_settings, name='sms_settings'),
    path('sms-inbox/', views.sms_inbox, name='sms_inbox'),
    path('sms-inbox/<int:pk>/read/', views.sms_mark_read, name='sms_mark_read'),
    path('sms-inbox/<int:pk>/delete/', views.sms_delete, name='sms_delete'),
]
