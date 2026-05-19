from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.conf import settings
from core.models import ClubStats, Officer, OfficerTitle, Sponsor, Announcement, TrailWorkLog, TrailWorkImage, ContactMessage, SiteSettings, EmailTemplate
from accounts.models import Member, RegistrationField
from core.email import send_test_email
from accounts.models import Member
from .forms import (
    ClubStatsForm, OfficerForm, SponsorForm,
    AnnouncementForm, TrailWorkLogForm,
)


def officer_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        if not (request.user.is_officer or request.user.is_site_admin or request.user.is_staff):
            messages.error(request, 'Officer access required.')
            return redirect('core:home')
        return view_func(request, *args, **kwargs)
    return wrapper


def site_admin_required(view_func):
    """Restricts to site admins (is_site_admin or is_staff) — for settings pages."""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        if not (request.user.is_site_admin or request.user.is_staff):
            messages.error(request, 'Site admin access required for this page.')
            return redirect('manage_panel:dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


# ── Dashboard ──────────────────────────────────────────────────────────────────

@officer_required
def dashboard(request):
    context = {
        'active_members': Member.objects.filter(membership_status='active').count(),
        'pending_members': Member.objects.filter(membership_status='pending').count(),
        'unread_messages': ContactMessage.objects.filter(is_read=False).count(),
        'officer_count': Officer.objects.count(),
        'sponsor_count': Sponsor.objects.filter(is_active=True).count(),
        'recent_logs': TrailWorkLog.objects.all()[:3],
        'recent_messages': ContactMessage.objects.filter(is_read=False)[:5],
        'pinned_announcements': Announcement.objects.filter(is_pinned=True).count(),
    }
    return render(request, 'manage_panel/dashboard.html', context)


# ── Club Stats ─────────────────────────────────────────────────────────────────

@officer_required
def stats_edit(request):
    stats, _ = ClubStats.objects.get_or_create(pk=1)
    if request.method == 'POST':
        form = ClubStatsForm(request.POST, instance=stats)
        if form.is_valid():
            form.save()
            messages.success(request, 'Club stats updated.')
            return redirect('manage_panel:stats_edit')
    else:
        form = ClubStatsForm(instance=stats)
    return render(request, 'manage_panel/stats_edit.html', {'form': form, 'stats': stats})


# ── Officer Titles ─────────────────────────────────────────────────────────────

@officer_required
def officer_title_list(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        if name:
            _, created = OfficerTitle.objects.get_or_create(
                name=name,
                defaults={'order': OfficerTitle.objects.count() + 1}
            )
            if created:
                messages.success(request, f'Title "{name}" added.')
            else:
                messages.warning(request, f'Title "{name}" already exists.')
        return redirect('manage_panel:officer_title_list')
    titles = OfficerTitle.objects.all()
    return render(request, 'manage_panel/officer_titles.html', {'titles': titles})


@officer_required
@require_POST
def officer_title_delete(request, pk):
    title = get_object_or_404(OfficerTitle, pk=pk)
    if Officer.objects.filter(title=title.name).exists():
        messages.error(request, f'Cannot delete "{title.name}" — officers are using it.')
    else:
        title.delete()
        messages.success(request, f'Title "{title.name}" deleted.')
    return redirect('manage_panel:officer_title_list')


# ── Officers ───────────────────────────────────────────────────────────────────

@officer_required
def officer_list(request):
    officers = Officer.objects.all()
    return render(request, 'manage_panel/officers/list.html', {'officers': officers})


@officer_required
def officer_add(request):
    if request.method == 'POST':
        form = OfficerForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Officer added.')
            return redirect('manage_panel:officer_list')
    else:
        form = OfficerForm()
    return render(request, 'manage_panel/officers/form.html', {'form': form, 'action': 'Add'})


@officer_required
def officer_edit(request, pk):
    officer = get_object_or_404(Officer, pk=pk)
    if request.method == 'POST':
        form = OfficerForm(request.POST, request.FILES, instance=officer)
        if form.is_valid():
            form.save()
            messages.success(request, f'{officer.name} updated.')
            return redirect('manage_panel:officer_list')
    else:
        form = OfficerForm(instance=officer)
    return render(request, 'manage_panel/officers/form.html', {'form': form, 'action': 'Edit', 'object': officer})


@officer_required
@require_POST
def officer_delete(request, pk):
    officer = get_object_or_404(Officer, pk=pk)
    name = officer.name
    officer.delete()
    messages.success(request, f'{name} removed.')
    return redirect('manage_panel:officer_list')


@officer_required
@require_POST
def officer_reorder(request):
    order = request.POST.getlist('order[]')
    for idx, pk in enumerate(order):
        Officer.objects.filter(pk=pk).update(order=idx)
    return JsonResponse({'status': 'ok'})


# ── Sponsors ───────────────────────────────────────────────────────────────────

@officer_required
def sponsor_list(request):
    sponsors = Sponsor.objects.all()
    return render(request, 'manage_panel/sponsors/list.html', {'sponsors': sponsors})


@officer_required
def sponsor_add(request):
    if request.method == 'POST':
        form = SponsorForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Sponsor added.')
            return redirect('manage_panel:sponsor_list')
    else:
        form = SponsorForm()
    return render(request, 'manage_panel/sponsors/form.html', {'form': form, 'action': 'Add'})


@officer_required
def sponsor_edit(request, pk):
    sponsor = get_object_or_404(Sponsor, pk=pk)
    if request.method == 'POST':
        form = SponsorForm(request.POST, request.FILES, instance=sponsor)
        if form.is_valid():
            form.save()
            messages.success(request, f'{sponsor.name} updated.')
            return redirect('manage_panel:sponsor_list')
    else:
        form = SponsorForm(instance=sponsor)
    return render(request, 'manage_panel/sponsors/form.html', {'form': form, 'action': 'Edit', 'object': sponsor})


@officer_required
@require_POST
def sponsor_delete(request, pk):
    sponsor = get_object_or_404(Sponsor, pk=pk)
    name = sponsor.name
    sponsor.delete()
    messages.success(request, f'{name} removed.')
    return redirect('manage_panel:sponsor_list')


@officer_required
@require_POST
def sponsor_toggle(request, pk):
    sponsor = get_object_or_404(Sponsor, pk=pk)
    sponsor.is_active = not sponsor.is_active
    sponsor.save()
    status = 'activated' if sponsor.is_active else 'deactivated'
    messages.success(request, f'{sponsor.name} {status}.')
    return redirect('manage_panel:sponsor_list')


# ── Announcements ──────────────────────────────────────────────────────────────

@officer_required
def announcement_list(request):
    announcements = Announcement.objects.all()
    return render(request, 'manage_panel/announcements/list.html', {'announcements': announcements})


def _zapier_post(announcement):
    import urllib.request, json
    cfg = SiteSettings.get()
    if cfg.facebook_integration != 'zapier' or not cfg.zapier_webhook_url:
        return
    if not announcement.is_public:
        return  # members-only announcements don't go to Facebook
    payload = json.dumps({
        'title': announcement.title,
        'body': announcement.body,
        'site_url': settings.SITE_URL,
    }).encode()
    try:
        req = urllib.request.Request(cfg.zapier_webhook_url, data=payload,
                                     headers={'Content-Type': 'application/json'})
        urllib.request.urlopen(req, timeout=5)
    except Exception:
        pass  # never block the user if Zapier is down


@officer_required
def announcement_add(request):
    if request.method == 'POST':
        form = AnnouncementForm(request.POST)
        if form.is_valid():
            ann = form.save()
            _zapier_post(ann)

            send_email = 'send_email' in request.POST
            send_text  = 'send_text'  in request.POST
            email_sent = text_sent = 0

            from core.email import send_email as _send_email, send_sms, _tmpl_override
            ann_url = f"{getattr(settings, 'SITE_URL', '').rstrip('/')}/announcements/{ann.pk}/"
            ann_tmpl_ctx = _tmpl_override('template_announcement')

            if send_email:
                active_members = Member.objects.filter(membership_status='active')
                for member in active_members:
                    try:
                        _send_email(
                            subject=f'Brainerd Snodeos: {ann.title}',
                            to=member.email,
                            template='announcement',
                            context={'announcement': ann, 'ann_url': ann_url, **ann_tmpl_ctx},
                        )
                        email_sent += 1
                    except Exception:
                        pass

            if send_text:
                snippet = ann.body[:120] + ('…' if len(ann.body) > 120 else '')
                sms_body = f'Brainerd Snodeos: {ann.title}\n{snippet}\n{ann_url}'
                recipients = Member.objects.filter(membership_status='active', accepts_texts=True).exclude(phone='')
                for m in recipients:
                    if send_sms(sms_body, m.phone):
                        text_sent += 1

            parts = ['Announcement posted.']
            if email_sent:  parts.append(f'Emailed {email_sent} members.')
            if text_sent:   parts.append(f'Texted {text_sent} members.')
            messages.success(request, ' '.join(parts))
            return redirect('manage_panel:announcement_list')
    else:
        form = AnnouncementForm()

    cfg = SiteSettings.get()
    return render(request, 'manage_panel/announcements/form.html', {
        'form': form,
        'action': 'New',
        'sms_configured': cfg.sms_configured,
        'opted_in_count': Member.objects.filter(membership_status='active', accepts_texts=True).exclude(phone='').count(),
        'active_count': Member.objects.filter(membership_status='active').count(),
    })


@officer_required
def announcement_edit(request, pk):
    announcement = get_object_or_404(Announcement, pk=pk)
    if request.method == 'POST':
        form = AnnouncementForm(request.POST, instance=announcement)
        if form.is_valid():
            form.save()
            messages.success(request, 'Announcement updated.')
            return redirect('manage_panel:announcement_list')
    else:
        form = AnnouncementForm(instance=announcement)
    return render(request, 'manage_panel/announcements/form.html', {'form': form, 'action': 'Edit', 'object': announcement})


@officer_required
@require_POST
def announcement_delete(request, pk):
    announcement = get_object_or_404(Announcement, pk=pk)
    announcement.delete()
    messages.success(request, 'Announcement deleted.')
    return redirect('manage_panel:announcement_list')


@officer_required
@require_POST
def announcement_pin(request, pk):
    announcement = get_object_or_404(Announcement, pk=pk)
    announcement.is_pinned = not announcement.is_pinned
    announcement.save()
    action = 'pinned' if announcement.is_pinned else 'unpinned'
    messages.success(request, f'Announcement {action}.')
    return redirect('manage_panel:announcement_list')


# ── Trail Work ─────────────────────────────────────────────────────────────────

@officer_required
def trail_work_list(request):
    logs = TrailWorkLog.objects.all()
    return render(request, 'manage_panel/trail_work/list.html', {'logs': logs})


@officer_required
def trail_work_add(request):
    if request.method == 'POST':
        form = TrailWorkLogForm(request.POST)
        if form.is_valid():
            log = form.save()
            for img in request.FILES.getlist('images'):
                TrailWorkImage.objects.create(log=log, image=img)
            messages.success(request, 'Trail work log added.')
            return redirect('manage_panel:trail_work_list')
    else:
        form = TrailWorkLogForm()
    return render(request, 'manage_panel/trail_work/form.html', {'form': form, 'action': 'Add'})


@officer_required
def trail_work_edit(request, pk):
    log = get_object_or_404(TrailWorkLog, pk=pk)
    if request.method == 'POST':
        form = TrailWorkLogForm(request.POST, instance=log)
        if form.is_valid():
            form.save()
            for img in request.FILES.getlist('images'):
                TrailWorkImage.objects.create(log=log, image=img)
            messages.success(request, 'Trail work log updated.')
            return redirect('manage_panel:trail_work_list')
    else:
        form = TrailWorkLogForm(instance=log)
    return render(request, 'manage_panel/trail_work/form.html', {
        'form': form, 'action': 'Edit', 'object': log,
        'existing_images': log.images.all(),
    })


@officer_required
@require_POST
def trail_work_image_delete(request, pk):
    img = get_object_or_404(TrailWorkImage, pk=pk)
    log_pk = img.log_id
    img.image.delete(save=False)
    img.delete()
    messages.success(request, 'Image removed.')
    return redirect('manage_panel:trail_work_edit', pk=log_pk)


@officer_required
@require_POST
def trail_work_delete(request, pk):
    log = get_object_or_404(TrailWorkLog, pk=pk)
    log.delete()
    messages.success(request, 'Trail work log deleted.')
    return redirect('manage_panel:trail_work_list')


# ── Contact Messages ───────────────────────────────────────────────────────────

@officer_required
def message_list(request):
    show = request.GET.get('show', 'unread')
    if show == 'all':
        msgs = ContactMessage.objects.all()
    else:
        msgs = ContactMessage.objects.filter(is_read=False)
    return render(request, 'manage_panel/messages/list.html', {'msgs': msgs, 'show': show})


@officer_required
def message_detail(request, pk):
    msg = get_object_or_404(ContactMessage, pk=pk)
    if not msg.is_read:
        msg.is_read = True
        msg.save()
    return render(request, 'manage_panel/messages/detail.html', {'msg': msg})


@officer_required
@require_POST
def message_delete(request, pk):
    msg = get_object_or_404(ContactMessage, pk=pk)
    msg.delete()
    messages.success(request, 'Message deleted.')
    return redirect('manage_panel:message_list')


# ── Member CSV Import ──────────────────────────────────────────────────────────

@officer_required
def member_import(request):
    import csv, io
    results = None

    if request.method == 'POST' and request.FILES.get('csv_file'):
        f = request.FILES['csv_file']
        text = io.TextIOWrapper(f, encoding='utf-8-sig', errors='replace')
        reader = csv.DictReader(text)
        created = skipped = errors = 0
        error_rows = []

        for i, row in enumerate(reader, start=2):
            email = (row.get('email') or row.get('Email') or '').strip().lower()
            if not email:
                errors += 1
                error_rows.append(f'Row {i}: missing email')
                continue
            if Member.objects.filter(email=email).exists():
                skipped += 1
                continue
            try:
                accepts_raw = (row.get('accepts_texts') or '').strip().lower()
                accepts_texts = True if accepts_raw in ('yes', 'y', '1', 'true') else (False if accepts_raw in ('no', 'n', '0', 'false') else None)
                num_sleds_raw = (row.get('num_snowmobiles') or '').strip()
                Member.objects.create_user(
                    email=email,
                    password=None,
                    first_name=(row.get('first_name') or row.get('First Name') or '').strip(),
                    last_name=(row.get('last_name') or row.get('Last Name') or '').strip(),
                    phone=(row.get('phone') or row.get('Phone') or '').strip(),
                    city=(row.get('city') or row.get('City') or '').strip(),
                    state=(row.get('state') or row.get('State') or 'MN').strip(),
                    zip_code=(row.get('zip_code') or row.get('Zip') or '').strip(),
                    snowmobile_brand=(row.get('snowmobile_brand') or row.get('Sled') or '').strip().lower(),
                    num_snowmobiles=int(num_sleds_raw) if num_sleds_raw.isdigit() else None,
                    accepts_texts=accepts_texts,
                    referral_source=(row.get('referral_source') or '').strip(),
                    membership_status=(row.get('membership_status') or row.get('Status') or 'active').strip().lower(),
                    membership_year=int(row['membership_year']) if (row.get('membership_year') or '').strip().isdigit() else None,
                )
                created += 1
            except Exception as e:
                errors += 1
                error_rows.append(f'Row {i} ({email}): {e}')

        results = {'created': created, 'skipped': skipped, 'errors': errors, 'error_rows': error_rows}

    return render(request, 'manage_panel/member_import.html', {'results': results})


# ── Registration Form Builder ──────────────────────────────────────────────────

@officer_required
def registration_form_settings(request):
    fields = RegistrationField.objects.all()

    if request.method == 'POST':
        for field in fields:
            field.is_enabled  = f'enabled_{field.field_name}'  in request.POST
            field.is_required = f'required_{field.field_name}' in request.POST
            field.label = request.POST.get(f'label_{field.field_name}', '').strip()
            field.save()
        messages.success(request, 'Registration form updated.')
        return redirect('manage_panel:registration_form_settings')

    return render(request, 'manage_panel/registration_form.html', {'fields': fields})


# ── Dues Management ────────────────────────────────────────────────────────────

@officer_required
def dues(request):
    import datetime
    from django.core.mail import send_mail

    active = Member.objects.filter(membership_status='active').order_by('last_name', 'first_name')

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'mark_paid':
            ids = request.POST.getlist('member_ids')
            if ids:
                today = datetime.date.today()
                Member.objects.filter(pk__in=ids).update(dues_paid=True, dues_paid_date=today)
                messages.success(request, f'{len(ids)} member(s) marked as dues paid.')

        elif action == 'mark_unpaid':
            ids = request.POST.getlist('member_ids')
            if ids:
                Member.objects.filter(pk__in=ids).update(dues_paid=False, dues_paid_date=None)
                messages.success(request, f'{len(ids)} member(s) marked as unpaid.')

        elif action == 'reset_all':
            active.update(dues_paid=False, dues_paid_date=None)
            messages.success(request, 'All members reset to unpaid (new dues year).')

        elif action == 'send_reminder':
            unpaid = active.filter(dues_paid=False)
            sent = 0
            for member in unpaid:
                try:
                    send_mail(
                        subject='Brainerd Snodeos — Dues Reminder',
                        message=(
                            f'Hi {member.first_name},\n\n'
                            'This is a friendly reminder that your Brainerd Snodeos '
                            'membership dues are outstanding.\n\n'
                            'Please contact an officer or visit our next monthly meeting '
                            '(every third Monday at 7:00 PM) to pay your dues.\n\n'
                            'Thank you for being a member!\n\n'
                            'Brainerd Snodeos Snowmobile Club'
                        ),
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[member.email],
                        fail_silently=True,
                    )
                    sent += 1
                except Exception:
                    pass
            messages.success(request, f'Dues reminder sent to {sent} unpaid member(s).')

        return redirect('manage_panel:dues')

    unpaid_count = active.filter(dues_paid=False).count()
    paid_count   = active.filter(dues_paid=True).count()
    return render(request, 'manage_panel/dues.html', {
        'members': active,
        'unpaid_count': unpaid_count,
        'paid_count': paid_count,
    })


# ── Permissions ────────────────────────────────────────────────────────────────

@site_admin_required
def permissions(request):
    if request.method == 'POST':
        member_id = request.POST.get('member_id')
        action    = request.POST.get('action')
        member = get_object_or_404(Member, pk=member_id)

        if action == 'grant_officer':
            member.is_officer = True
            member.save()
            messages.success(request, f'{member.get_full_name()} granted Officer access.')
        elif action == 'grant_admin':
            member.is_officer = True
            member.is_site_admin = True
            member.save()
            messages.success(request, f'{member.get_full_name()} granted Site Admin access.')
        elif action == 'revoke':
            if member == request.user:
                messages.error(request, "You can't revoke your own access.")
            elif member.is_staff:
                messages.error(request, "Cannot modify a superuser.")
            else:
                member.is_officer = False
                member.is_site_admin = False
                member.save()
                messages.success(request, f'{member.get_full_name()} access revoked.')
        return redirect('manage_panel:permissions')
    members = Member.objects.filter(membership_status='active').order_by('last_name', 'first_name')
    return render(request, 'manage_panel/permissions.html', {'members': members})


# ── Facebook Integration ───────────────────────────────────────────────────────

@site_admin_required
def facebook_settings(request):
    cfg = SiteSettings.get()
    if request.method == 'POST':
        cfg.facebook_integration = request.POST.get('facebook_integration', 'none')
        cfg.facebook_page_url    = request.POST.get('facebook_page_url', '').strip()
        cfg.facebook_app_id      = request.POST.get('facebook_app_id', '').strip()
        cfg.zapier_webhook_url   = request.POST.get('zapier_webhook_url', '').strip()
        cfg.save()
        messages.success(request, 'Facebook integration settings saved.')
        return redirect('manage_panel:facebook_settings')
    return render(request, 'manage_panel/facebook_settings.html', {'cfg': cfg})


# ── Email Blast ────────────────────────────────────────────────────────────────

@officer_required
def email_blast(request):
    from core.email import send_email as _send_email
    import re
    recipients = Member.objects.filter(membership_status='active')

    templates = EmailTemplate.objects.all()

    if request.method == 'POST':
        subject   = request.POST.get('subject', '').strip()
        blast_html = request.POST.get('body_html', '').strip()
        if not subject or not blast_html:
            messages.error(request, 'Subject and body are required.')
        else:
            # Resolve selected template for branding overrides
            tmpl_id = request.POST.get('template_id')
            tmpl = None
            if tmpl_id:
                tmpl = EmailTemplate.objects.filter(pk=tmpl_id).first()
            if not tmpl:
                tmpl = EmailTemplate.get_default()

            blast_plain = re.sub(r'<[^>]+>', '', blast_html).strip()
            extra_ctx = {}
            if tmpl:
                extra_ctx = {
                    'email_from_name':        tmpl.from_name,
                    'email_header_color':     tmpl.header_color,
                    'email_accent_color':     tmpl.accent_color,
                    'email_header_image_url': tmpl.header_image_url,
                    'email_footer_text':      tmpl.footer_text,
                }
            sent = failed = 0
            for member in recipients:
                try:
                    _send_email(
                        subject=subject,
                        to=member.email,
                        template='blast',
                        context={'blast_body': blast_html, 'blast_plain': blast_plain, **extra_ctx},
                    )
                    sent += 1
                except Exception:
                    failed += 1
            if failed:
                messages.warning(request, f'Sent to {sent} members. {failed} failed.')
            else:
                messages.success(request, f'Email sent to {sent} active members.')
            return redirect('manage_panel:email_blast')

    return render(request, 'manage_panel/email_blast.html', {
        'recipient_count': recipients.count(),
        'templates': templates,
        'default_tmpl': EmailTemplate.get_default(),
    })


# ── Email Settings → redirect to Communications ────────────────────────────────

@officer_required
def email_settings(request):
    return redirect('manage_panel:communications')


# ── Communications Setup ───────────────────────────────────────────────────────

@site_admin_required
def communications(request):
    cfg = SiteSettings.get()

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'save_email':
            cfg.brevo_smtp_key     = request.POST.get('brevo_smtp_key', '').strip()
            cfg.resend_api_key     = request.POST.get('resend_api_key', '').strip()
            cfg.notification_email = request.POST.get('notification_email', '').strip()
            cfg.save()
            messages.success(request, 'Email settings saved.')

        elif action == 'save_sms':
            cfg.brevo_api_key      = request.POST.get('brevo_api_key', '').strip()
            cfg.twilio_account_sid = request.POST.get('twilio_account_sid', '').strip()
            cfg.twilio_auth_token  = request.POST.get('twilio_auth_token', '').strip()
            cfg.twilio_from_number = request.POST.get('twilio_from_number', '').strip()
            cfg.save()
            messages.success(request, 'SMS settings saved.')

        elif action == 'save_branding':
            cfg.email_from_name    = request.POST.get('email_from_name', '').strip()
            cfg.email_header_color = request.POST.get('email_header_color', '#1363A2').strip()
            cfg.email_accent_color = request.POST.get('email_accent_color', '#1363A2').strip()
            cfg.email_footer_text  = request.POST.get('email_footer_text', '').strip()
            cfg.save()
            messages.success(request, 'Email appearance saved.')

        elif action == 'save_templates':
            def _get_tmpl(key):
                val = request.POST.get(key, '').strip()
                return EmailTemplate.objects.filter(pk=val).first() if val else None
            cfg.template_contact_reply  = _get_tmpl('template_contact_reply')
            cfg.template_member         = _get_tmpl('template_member')
            cfg.template_announcement   = _get_tmpl('template_announcement')
            cfg.save()
            messages.success(request, 'Template assignments saved.')

        elif action == 'test_email':
            recipient = request.POST.get('test_recipient', '').strip() or request.user.email
            try:
                send_test_email(recipient)
                messages.success(request, f'Test email sent to {recipient}. Check your inbox (and spam folder).')
            except Exception as exc:
                messages.error(request, f'Failed: {exc}')

        return redirect('manage_panel:communications')

    email_templates = EmailTemplate.objects.all()
    return render(request, 'manage_panel/communications.html', {
        'cfg': cfg,
        'email_templates': email_templates,
    })


# ── Setup Guide ────────────────────────────────────────────────────────────────

@officer_required
def setup_guide(request):
    checklist = [
        {'text': 'Configure email & SMS in Settings → Communications',          'url': reverse('manage_panel:communications')},
        {'text': 'Send a test email from the Communications page',               'url': reverse('manage_panel:communications')},
        {'text': 'Add real officer names, photos, phone & email in Officers',    'url': reverse('manage_panel:officer_list')},
        {'text': 'Update club stats in Overview → Club Stats',                   'url': reverse('manage_panel:stats_edit')},
        {'text': 'Add current sponsors with logos in Club → Sponsors',           'url': reverse('manage_panel:sponsor_list')},
        {'text': 'Post a welcome announcement in Content → Announcements',       'url': reverse('manage_panel:announcement_list')},
        {'text': 'Review registration form fields in People → Registration Form','url': reverse('manage_panel:registration_form_settings')},
        {'text': 'Approve or import existing members in People → All Members',   'url': reverse('members:member_list')},
        {'text': 'Configure Facebook integration in Settings → Facebook',        'url': reverse('manage_panel:facebook_settings')},
        {'text': 'Update domain/DNS when pointing to a custom domain',           'url': None},
        {'text': 'Set DEBUG=False in .env when ready for public use',            'url': None},
    ]
    env_vars = [
        {'name': 'SECRET_KEY',              'purpose': 'Django security key — keep private, never share', 'example': '50-char random string'},
        {'name': 'DEBUG',                   'purpose': 'Must be False in production',                     'example': 'False'},
        {'name': 'ALLOWED_HOSTS',           'purpose': 'Comma-separated allowed domain names',            'example': 'snodeos.com,www.snodeos.com'},
        {'name': 'DATABASE_URL',            'purpose': 'PostgreSQL connection string',                    'example': 'postgresql://user:pass@db/snodeos'},
        {'name': 'CSRF_TRUSTED_ORIGINS',    'purpose': 'Domains allowed to submit forms',                 'example': 'https://snodeos.com'},
        {'name': 'SITE_URL',                'purpose': 'Full public URL (used in email links)',            'example': 'https://snodeos.com'},
        {'name': 'DEFAULT_FROM_EMAIL',      'purpose': '"From" name on system emails',                    'example': 'Brainerd Snodeos <noreply@snodeos.com>'},
        {'name': 'CLOUDFLARE_TUNNEL_TOKEN', 'purpose': 'Cloudflare tunnel token (if using tunnel)',       'example': 'eyJh...'},
    ]
    return render(request, 'manage_panel/setup_guide.html', {
        'checklist': checklist,
        'env_vars': env_vars,
    })


# ── Text Members ───────────────────────────────────────────────────────────────

@officer_required
def text_members(request):
    from core.email import send_sms
    cfg = SiteSettings.get()
    sms_configured = cfg.sms_configured

    if request.method == 'POST' and sms_configured:
        message = request.POST.get('message', '').strip()
        if message:
            recipients = Member.objects.filter(membership_status='active', accepts_texts=True).exclude(phone='')
            sent = failed = 0
            for member in recipients:
                if send_sms(message, member.phone):
                    sent += 1
                else:
                    failed += 1
            if failed:
                messages.warning(request, f'Sent to {sent} members. {failed} failed.')
            else:
                messages.success(request, f'Text sent to {sent} members who opted in.')
            return redirect('manage_panel:text_members')

    opted_in = Member.objects.filter(membership_status='active', accepts_texts=True).exclude(phone='').count()
    return render(request, 'manage_panel/text_members.html', {
        'sms_configured': sms_configured,
        'opted_in': opted_in,
    })


# ── SMS Settings → redirect to Communications ──────────────────────────────────

@officer_required
def sms_settings(request):
    return redirect('manage_panel:communications')


# ── Email Templates ────────────────────────────────────────────────────────────

@site_admin_required
def email_template_list(request):
    """List all email templates; seed a default one from SiteSettings if none exist."""
    if not EmailTemplate.objects.exists():
        cfg = SiteSettings.get()
        EmailTemplate.objects.create(
            name='Default',
            description='Standard Brainerd Snodeos branded email',
            from_name=cfg.email_from_name or 'Brainerd Snodeos',
            header_color=cfg.email_header_color or '#1363A2',
            accent_color=cfg.email_accent_color or '#1363A2',
            footer_text=cfg.email_footer_text or "You're receiving this as a member of the Brainerd Snodeos.",
            is_default=True,
        )
    templates = EmailTemplate.objects.all()
    return render(request, 'manage_panel/email_templates/list.html', {'templates': templates})


@site_admin_required
def email_template_add(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        if not name:
            messages.error(request, 'Template name is required.')
        else:
            tmpl = EmailTemplate.objects.create(
                name=name,
                description=request.POST.get('description', '').strip(),
                from_name=request.POST.get('from_name', 'Brainerd Snodeos').strip(),
                header_color=request.POST.get('header_color', '#1363A2').strip(),
                accent_color=request.POST.get('accent_color', '#1363A2').strip(),
                header_image_url=request.POST.get('header_image_url', '').strip(),
                footer_text=request.POST.get('footer_text', '').strip(),
                is_default='is_default' in request.POST,
            )
            messages.success(request, f'Template "{tmpl.name}" created.')
            return redirect('manage_panel:email_template_list')
    # Pre-fill from default if available
    default = EmailTemplate.get_default()
    return render(request, 'manage_panel/email_templates/form.html', {'action': 'New', 'tmpl': default})


@site_admin_required
def email_template_edit(request, pk):
    tmpl = get_object_or_404(EmailTemplate, pk=pk)
    if request.method == 'POST':
        tmpl.name             = request.POST.get('name', '').strip() or tmpl.name
        tmpl.description      = request.POST.get('description', '').strip()
        tmpl.from_name        = request.POST.get('from_name', '').strip()
        tmpl.header_color     = request.POST.get('header_color', '#1363A2').strip()
        tmpl.accent_color     = request.POST.get('accent_color', '#1363A2').strip()
        tmpl.header_image_url = request.POST.get('header_image_url', '').strip()
        tmpl.footer_text      = request.POST.get('footer_text', '').strip()
        tmpl.is_default       = 'is_default' in request.POST
        tmpl.save()
        messages.success(request, f'Template "{tmpl.name}" updated.')
        return redirect('manage_panel:email_template_list')
    return render(request, 'manage_panel/email_templates/form.html', {'action': 'Edit', 'tmpl': tmpl})


@site_admin_required
@require_POST
def email_template_delete(request, pk):
    tmpl = get_object_or_404(EmailTemplate, pk=pk)
    if tmpl.is_default and EmailTemplate.objects.count() > 1:
        messages.error(request, 'Cannot delete the default template. Set another template as default first.')
    else:
        tmpl.delete()
        messages.success(request, 'Template deleted.')
    return redirect('manage_panel:email_template_list')


@site_admin_required
def email_template_api(request, pk):
    """JSON endpoint — returns template fields for the blast form's JS selector."""
    tmpl = get_object_or_404(EmailTemplate, pk=pk)
    from django.http import JsonResponse
    return JsonResponse({
        'from_name':    tmpl.from_name,
        'header_color': tmpl.header_color,
        'accent_color': tmpl.accent_color,
        'footer_text':  tmpl.footer_text,
    })
