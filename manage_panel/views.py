from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.conf import settings
from core.models import ClubStats, Officer, OfficerTitle, Sponsor, Announcement, AnnouncementImage, TrailCondition, TrailConditionImage, TrailWorkLog, TrailWorkImage, ContactMessage, SiteSettings, EmailTemplate, AuditLog, EmailLog, InboundSMS, TrailSegment, Event, EquipmentItem
from accounts.models import Member, RegistrationField, MemberGroup
from core.email import send_test_email
from core.geo import create_image_with_gps
from accounts.models import Member
from .forms import (
    ClubStatsForm, OfficerForm, SponsorForm,
    AnnouncementForm, TrailConditionForm, TrailWorkLogForm,
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
        form = AnnouncementForm(request.POST, request.FILES)
        if form.is_valid():
            ann = form.save()
            for img in request.FILES.getlist('images'):
                create_image_with_gps(AnnouncementImage, img, announcement=ann)
            _zapier_post(ann)

            send_email = 'send_email' in request.POST
            send_text  = 'send_text'  in request.POST
            email_sent = text_sent = 0

            from core.email import send_email as _send_email, send_sms, _tmpl_override
            ann_url = f"{getattr(settings, 'SITE_URL', '').rstrip('/')}/announcements/{ann.pk}/"
            ann_tmpl_ctx = _tmpl_override('template_announcement')
            image_urls = [i.absolute_url for i in ann.images.all()]

            if send_email:
                active_members = Member.objects.filter(membership_status='active')
                for member in active_members:
                    if _send_email(
                        subject=f'Brainerd Snodeos: {ann.title}',
                        to=member.email,
                        template='announcement',
                        context={'announcement': ann, 'ann_url': ann_url, 'image_urls': image_urls, **ann_tmpl_ctx},
                    ):
                        email_sent += 1

            if send_text:
                snippet = ann.body[:120] + ('…' if len(ann.body) > 120 else '')
                sms_body = f'Brainerd Snodeos: {ann.title}\n{snippet}\n{ann_url}'
                recipients = Member.objects.filter(membership_status='active', accepts_texts=True).exclude(phone='')
                for m in recipients:
                    if send_sms(sms_body, m.phone):
                        text_sent += 1

            if email_sent or text_sent:
                from core.audit import log_action
                log_action(request.user, 'announcement_send',
                           target=ann.title,
                           detail=f'Emails: {email_sent}, Texts: {text_sent}')
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
        form = AnnouncementForm(request.POST, request.FILES, instance=announcement)
        if form.is_valid():
            form.save()
            for img in request.FILES.getlist('images'):
                create_image_with_gps(AnnouncementImage, img, announcement=announcement)
            messages.success(request, 'Announcement updated.')
            return redirect('manage_panel:announcement_list')
    else:
        form = AnnouncementForm(instance=announcement)
    return render(request, 'manage_panel/announcements/form.html', {
        'form': form, 'action': 'Edit', 'object': announcement,
        'existing_images': announcement.images.all(),
    })


@officer_required
@require_POST
def announcement_image_delete(request, pk):
    img = get_object_or_404(AnnouncementImage, pk=pk)
    ann_pk = img.announcement_id
    img.image.delete(save=False)
    img.delete()
    messages.success(request, 'Photo removed.')
    return redirect('manage_panel:announcement_edit', pk=ann_pk)


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


# ── Trail Conditions ───────────────────────────────────────────────────────────

@officer_required
def trail_condition_list(request):
    conditions = TrailCondition.objects.all()
    return render(request, 'manage_panel/trail_conditions/list.html', {'conditions': conditions})


def _zapier_post_trail(condition):
    import urllib.request, json
    cfg = SiteSettings.get()
    if cfg.facebook_integration != 'zapier' or not cfg.zapier_webhook_url:
        return
    if not condition.is_public:
        return
    payload = json.dumps({
        'title': f'Trail Update: {condition.title}',
        'body': f'Status: {condition.get_status_display()}\n\n{condition.body}',
        'site_url': settings.SITE_URL,
    }).encode()
    try:
        req = urllib.request.Request(cfg.zapier_webhook_url, data=payload,
                                     headers={'Content-Type': 'application/json'})
        urllib.request.urlopen(req, timeout=5)
    except Exception:
        pass


@officer_required
def trail_condition_add(request):
    # ?lat=&lng= query params pre-fill (set by "click map → create here" flow)
    initial = {}
    try:
        if request.GET.get('lat'): initial['lat'] = float(request.GET['lat'])
        if request.GET.get('lng'): initial['lng'] = float(request.GET['lng'])
    except (ValueError, TypeError):
        initial = {}
    if request.method == 'POST':
        form = TrailConditionForm(request.POST, request.FILES)
        if form.is_valid():
            condition = form.save()
            for img in request.FILES.getlist('images'):
                create_image_with_gps(TrailConditionImage, img, condition=condition)
            _zapier_post_trail(condition)

            send_email = 'send_email' in request.POST
            send_text  = 'send_text'  in request.POST
            email_sent = text_sent = 0

            from core.email import send_email as _send_email, send_sms, _tmpl_override
            cond_url = f"{getattr(settings, 'SITE_URL', '').rstrip('/')}/trail-conditions/{condition.pk}/"
            tmpl_ctx = _tmpl_override('template_trail_condition') or _tmpl_override('template_announcement')
            image_urls = [i.absolute_url for i in condition.images.all()]

            if send_email:
                active_members = Member.objects.filter(membership_status='active')
                for member in active_members:
                    if _send_email(
                        subject=f'Trail Update: {condition.title}',
                        to=member.email,
                        template='trail_condition',
                        context={'condition': condition, 'cond_url': cond_url, 'image_urls': image_urls, **tmpl_ctx},
                    ):
                        email_sent += 1

            if send_text:
                status_label = condition.get_status_display()
                snippet = condition.body[:100] + ('…' if len(condition.body) > 100 else '')
                sms_body = f'Trail Update [{status_label}]: {condition.title}'
                if snippet:
                    sms_body += f'\n{snippet}'
                sms_body += f'\n{cond_url}'
                recipients = Member.objects.filter(membership_status='active', accepts_texts=True).exclude(phone='')
                for m in recipients:
                    if send_sms(sms_body, m.phone):
                        text_sent += 1

            if email_sent or text_sent:
                from core.audit import log_action
                log_action(request.user, 'trail_condition_send',
                           target=condition.title,
                           detail=f'Status: {condition.get_status_display()}, Emails: {email_sent}, Texts: {text_sent}')
            parts = ['Trail condition posted.']
            if email_sent:  parts.append(f'Emailed {email_sent} members.')
            if text_sent:   parts.append(f'Texted {text_sent} members.')
            messages.success(request, ' '.join(parts))
            return redirect('manage_panel:trail_condition_list')
    else:
        form = TrailConditionForm(initial=initial)

    cfg = SiteSettings.get()
    return render(request, 'manage_panel/trail_conditions/form.html', {
        'form': form,
        'action': 'New',
        'sms_configured': cfg.sms_configured,
        'opted_in_count': Member.objects.filter(membership_status='active', accepts_texts=True).exclude(phone='').count(),
        'active_count': Member.objects.filter(membership_status='active').count(),
    })


@officer_required
def trail_condition_edit(request, pk):
    condition = get_object_or_404(TrailCondition, pk=pk)
    if request.method == 'POST':
        form = TrailConditionForm(request.POST, request.FILES, instance=condition)
        if form.is_valid():
            form.save()
            for img in request.FILES.getlist('images'):
                create_image_with_gps(TrailConditionImage, img, condition=condition)
            messages.success(request, 'Trail condition updated.')
            return redirect('manage_panel:trail_condition_list')
    else:
        form = TrailConditionForm(instance=condition)
    return render(request, 'manage_panel/trail_conditions/form.html', {
        'form': form, 'action': 'Edit', 'object': condition,
        'existing_images': condition.images.all(),
    })


@officer_required
@require_POST
def trail_condition_image_delete(request, pk):
    img = get_object_or_404(TrailConditionImage, pk=pk)
    cond_pk = img.condition_id
    img.image.delete(save=False)
    img.delete()
    messages.success(request, 'Photo removed.')
    return redirect('manage_panel:trail_condition_edit', pk=cond_pk)


@officer_required
@require_POST
def trail_condition_delete(request, pk):
    condition = get_object_or_404(TrailCondition, pk=pk)
    condition.delete()
    messages.success(request, 'Trail condition deleted.')
    return redirect('manage_panel:trail_condition_list')


@officer_required
@require_POST
def trail_condition_pin(request, pk):
    condition = get_object_or_404(TrailCondition, pk=pk)
    condition.is_pinned = not condition.is_pinned
    condition.save()
    action = 'pinned' if condition.is_pinned else 'unpinned'
    messages.success(request, f'Trail condition {action}.')
    return redirect('manage_panel:trail_condition_list')


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
                create_image_with_gps(TrailWorkImage, img, log=log)
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
                create_image_with_gps(TrailWorkImage, img, log=log)
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
    from core.throttle import throttle
    import re

    templates = EmailTemplate.objects.all()
    groups = MemberGroup.objects.prefetch_related('members').all()

    if request.method == 'POST':
        # 5 blasts per officer per hour — guards against double-clicks and spam
        if not throttle(f'email_blast:{request.user.pk}', max_count=5, window_seconds=3600):
            messages.error(request, "You've sent several blasts recently. Wait a bit before sending another.")
            return redirect('manage_panel:email_blast')

        # Recipient selection: either "all active" or a specific group
        group_id = request.POST.get('group_id', '').strip()
        if group_id:
            group = MemberGroup.objects.filter(pk=group_id).first()
            recipients = group.members.filter(membership_status='active') if group else Member.objects.none()
            audience_label = f'group "{group.name}"' if group else 'no one (invalid group)'
        else:
            recipients = Member.objects.filter(membership_status='active')
            audience_label = 'all active members'

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
                if _send_email(
                    subject=subject,
                    to=member.email,
                    template='blast',
                    context={'blast_body': blast_html, 'blast_plain': blast_plain, **extra_ctx},
                ):
                    sent += 1
                else:
                    failed += 1
            from core.audit import log_action
            log_action(request.user, 'email_blast',
                       target=subject,
                       detail=f'Audience: {audience_label}, Sent: {sent}, Failed: {failed}, Template: {tmpl.name if tmpl else "default"}')
            if failed:
                messages.warning(request, f'Sent to {sent} ({audience_label}). {failed} failed.')
            else:
                messages.success(request, f'Email sent to {sent} ({audience_label}).')
            return redirect('manage_panel:email_blast')

    return render(request, 'manage_panel/email_blast.html', {
        'recipient_count': Member.objects.filter(membership_status='active').count(),
        'templates': templates,
        'groups': groups,
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

        elif action == 'save_social':
            cfg.site_description = request.POST.get('site_description', '').strip()
            if request.POST.get('clear_social_image') == '1' and cfg.social_image:
                cfg.social_image.delete(save=False)
                cfg.social_image = None
            if request.FILES.get('social_image'):
                cfg.social_image = request.FILES['social_image']
            cfg.save()
            messages.success(request, 'Social / link-preview settings saved.')

        elif action == 'save_map':
            try:
                cfg.map_default_lat  = float(request.POST.get('map_default_lat', cfg.map_default_lat))
                cfg.map_default_lng  = float(request.POST.get('map_default_lng', cfg.map_default_lng))
                cfg.map_default_zoom = int(request.POST.get('map_default_zoom', cfg.map_default_zoom))
                cfg.save()
                messages.success(request, 'Map default location saved.')
            except (ValueError, TypeError):
                messages.error(request, 'Invalid coordinates — must be decimal numbers.')

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
    cfg = SiteSettings.get()

    # Handle the inline test-email button at the top of the setup page
    if request.method == 'POST' and request.POST.get('action') == 'test_email':
        recipient = request.POST.get('test_recipient', '').strip() or request.user.email
        if not cfg.email_configured:
            messages.error(request, 'Email is not configured yet — set up Brevo or Resend first.')
        else:
            try:
                send_test_email(recipient)
                messages.success(request, f'Test email sent to {recipient}. Check your inbox (and spam folder).')
            except Exception as exc:
                messages.error(request, f'Failed to send: {exc}')
        return redirect('manage_panel:setup_guide')

    email_templates = EmailTemplate.objects.all()

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
        'cfg': cfg,
        'email_templates': email_templates,
        'default_test_recipient': request.user.email,
    })


# ── Text Members ───────────────────────────────────────────────────────────────

@officer_required
def text_members(request):
    from core.email import send_sms
    from core.throttle import throttle
    cfg = SiteSettings.get()
    sms_configured = cfg.sms_configured

    if request.method == 'POST' and sms_configured:
        if not throttle(f'sms_blast:{request.user.pk}', max_count=3, window_seconds=3600):
            messages.error(request, "You've sent several texts recently. Wait a bit before sending another.")
            return redirect('manage_panel:text_members')

        group_id = request.POST.get('group_id', '').strip()
        if group_id:
            group = MemberGroup.objects.filter(pk=group_id).first()
            base = group.members if group else Member.objects.none()
            audience_label = f'group "{group.name}"' if group else 'no one (invalid group)'
        else:
            base = Member.objects.all()
            audience_label = 'all opted-in members'

        message = request.POST.get('message', '').strip()
        if message:
            recipients = base.filter(membership_status='active', accepts_texts=True).exclude(phone='')
            sent = failed = 0
            for member in recipients:
                if send_sms(message, member.phone):
                    sent += 1
                else:
                    failed += 1
            from core.audit import log_action
            log_action(request.user, 'sms_blast',
                       target=message[:80],
                       detail=f'Audience: {audience_label}, Sent: {sent}, Failed: {failed}')
            if failed:
                messages.warning(request, f'Sent to {sent} ({audience_label}). {failed} failed.')
            else:
                messages.success(request, f'Text sent to {sent} ({audience_label}).')
            return redirect('manage_panel:text_members')

    opted_in = Member.objects.filter(membership_status='active', accepts_texts=True).exclude(phone='').count()
    groups = MemberGroup.objects.prefetch_related('members').all()
    return render(request, 'manage_panel/text_members.html', {
        'sms_configured': sms_configured,
        'opted_in': opted_in,
        'groups': groups,
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
            tmpl = EmailTemplate(
                name=name,
                description=request.POST.get('description', '').strip(),
                from_name=request.POST.get('from_name', 'Brainerd Snodeos').strip(),
                header_color=request.POST.get('header_color', '#1363A2').strip(),
                accent_color=request.POST.get('accent_color', '#1363A2').strip(),
                footer_text=request.POST.get('footer_text', '').strip(),
                is_default='is_default' in request.POST,
            )
            if 'header_image' in request.FILES:
                tmpl.header_image = request.FILES['header_image']
            tmpl.save()
            messages.success(request, f'Template "{tmpl.name}" created.')
            return redirect('manage_panel:email_template_list')
    default = EmailTemplate.get_default()
    return render(request, 'manage_panel/email_templates/form.html', {'action': 'New', 'tmpl': default})


@site_admin_required
def email_template_edit(request, pk):
    tmpl = get_object_or_404(EmailTemplate, pk=pk)
    if request.method == 'POST':
        tmpl.name         = request.POST.get('name', '').strip() or tmpl.name
        tmpl.description  = request.POST.get('description', '').strip()
        tmpl.from_name    = request.POST.get('from_name', '').strip()
        tmpl.header_color = request.POST.get('header_color', '#1363A2').strip()
        tmpl.accent_color = request.POST.get('accent_color', '#1363A2').strip()
        tmpl.footer_text  = request.POST.get('footer_text', '').strip()
        tmpl.is_default   = 'is_default' in request.POST
        if 'header_image' in request.FILES:
            tmpl.header_image = request.FILES['header_image']
        elif 'clear_header_image' in request.POST:
            tmpl.header_image.delete(save=False)
            tmpl.header_image = None
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


@site_admin_required
@require_POST
def email_template_test(request, pk):
    """Send a sample email rendered with this template's branding to the current user."""
    from core.email import send_email as _send_email
    tmpl = get_object_or_404(EmailTemplate, pk=pk)
    recipient = request.POST.get('test_recipient', '').strip() or request.user.email
    cfg = SiteSettings.get()
    if not cfg.email_configured:
        messages.error(request, 'Email is not configured — set up Brevo or Resend first.')
        return redirect('manage_panel:email_template_edit', pk=pk)
    try:
        _send_email(
            subject=f'[Template preview] {tmpl.name}',
            to=recipient,
            template='blast',
            context={
                'blast_body': '<p>This is a sample email so you can preview how the <strong>'
                              f'{tmpl.name}</strong> template will look in your inbox.</p>'
                              '<p>Replace this with real announcement content when you send a real blast.</p>',
                'blast_plain': f'Sample email previewing the "{tmpl.name}" template.',
                'email_from_name':        tmpl.from_name,
                'email_header_color':     tmpl.header_color,
                'email_accent_color':     tmpl.accent_color,
                'email_header_image_url': tmpl.header_image_url,
                'email_footer_text':      tmpl.footer_text,
            },
        )
        messages.success(request, f'Preview email sent to {recipient}.')
    except Exception as exc:
        messages.error(request, f'Failed to send: {exc}')
    return redirect('manage_panel:email_template_edit', pk=pk)


# ── Audit Log ──────────────────────────────────────────────────────────────────

@site_admin_required
def audit_log(request):
    """View recent admin actions. Site-admin only since it can reveal officer activity."""
    logs = AuditLog.objects.select_related('actor').all()[:200]
    return render(request, 'manage_panel/audit_log.html', {'logs': logs})


@officer_required
def sms_inbox(request):
    """Officer-facing inbox of incoming text messages from Twilio."""
    show = request.GET.get('show', 'unread')   # unread | all
    qs = InboundSMS.objects.all()
    if show == 'unread':
        qs = qs.filter(is_read=False)
    messages_list = list(qs[:200])
    unread_count = InboundSMS.objects.filter(is_read=False).count()
    total_count  = InboundSMS.objects.count()
    return render(request, 'manage_panel/sms_inbox.html', {
        'messages_list': messages_list,
        'show': show,
        'unread_count': unread_count,
        'total_count': total_count,
    })


@officer_required
@require_POST
def sms_mark_read(request, pk):
    msg = get_object_or_404(InboundSMS, pk=pk)
    msg.is_read = not msg.is_read
    msg.save()
    return redirect('manage_panel:sms_inbox')


@officer_required
@require_POST
def sms_delete(request, pk):
    msg = get_object_or_404(InboundSMS, pk=pk)
    msg.delete()
    messages.success(request, 'Text deleted.')
    return redirect('manage_panel:sms_inbox')


@site_admin_required
def email_log(request):
    """Recent email delivery history. Defaults to failures-only since that's what officers care about."""
    status_filter = request.GET.get('status', 'failed')
    logs = EmailLog.objects.all()
    if status_filter in ('success', 'failed'):
        logs = logs.filter(status=status_filter)
    logs = logs[:200]
    counts = {
        'failed':  EmailLog.objects.filter(status='failed').count(),
        'success': EmailLog.objects.filter(status='success').count(),
    }
    return render(request, 'manage_panel/email_log.html', {
        'logs': logs,
        'status_filter': status_filter,
        'counts': counts,
    })


# ── Trail Segments (map editor) ────────────────────────────────────────────────

@officer_required
def trail_segment_list(request):
    segments = TrailSegment.objects.all()
    return render(request, 'manage_panel/trail_segments/list.html', {'segments': segments})


@officer_required
def trail_segment_editor(request, pk=None):
    """One template, two modes: pk=None creates a new segment; pk loads an
    existing one for editing. The Leaflet map is the same either way."""
    segment = get_object_or_404(TrailSegment, pk=pk) if pk else None

    if request.method == 'POST':
        import json as _json
        geometry_raw = request.POST.get('geometry', '[]')
        try:
            geometry = _json.loads(geometry_raw)
            if not isinstance(geometry, list):
                geometry = []
        except _json.JSONDecodeError:
            geometry = []

        name = request.POST.get('name', '').strip()
        if not name:
            messages.error(request, 'Trail name is required.')
        elif not geometry:
            messages.error(request, 'Draw at least one trail line on the map.')
        else:
            if segment is None:
                segment = TrailSegment()
            segment.name        = name
            segment.description = request.POST.get('description', '').strip()
            segment.status      = request.POST.get('status', 'open')
            segment.difficulty  = request.POST.get('difficulty', '')
            segment.visibility  = request.POST.get('visibility', 'both')
            segment.color       = request.POST.get('color', '').strip()
            segment.geometry    = geometry
            if request.POST.get('mark_groomed_now'):
                from django.utils import timezone as _tz
                segment.groomed_at = _tz.now()
            segment.save()
            messages.success(request, f'Trail "{segment.name}" saved.')
            return redirect('manage_panel:trail_segment_list')

    return render(request, 'manage_panel/trail_segments/editor.html', {
        'segment': segment,
        'status_choices':     TrailSegment.STATUS_CHOICES,
        'visibility_choices': TrailSegment.VISIBILITY_CHOICES,
        'difficulty_choices': TrailSegment.DIFFICULTY_CHOICES,
    })


@officer_required
@require_POST
def trail_segment_delete(request, pk):
    seg = get_object_or_404(TrailSegment, pk=pk)
    name = seg.name
    seg.delete()
    messages.success(request, f'Trail "{name}" deleted.')
    return redirect('manage_panel:trail_segment_list')


# ── Member Groups ──────────────────────────────────────────────────────────────

@officer_required
def member_group_list(request):
    groups = MemberGroup.objects.prefetch_related('members').all()
    return render(request, 'manage_panel/member_groups/list.html', {'groups': groups})


@officer_required
def member_group_form(request, pk=None):
    group = get_object_or_404(MemberGroup, pk=pk) if pk else None

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        member_ids = request.POST.getlist('member_ids')

        if not name:
            messages.error(request, 'Group name is required.')
        else:
            if group is None:
                group = MemberGroup(name=name)
            else:
                group.name = name
            group.description = description
            try:
                group.save()
            except Exception as exc:
                messages.error(request, f'Could not save group: {exc}')
                return redirect('manage_panel:member_group_list')
            group.members.set(Member.objects.filter(pk__in=member_ids))
            messages.success(request, f'Group "{group.name}" saved with {group.members.count()} member(s).')
            return redirect('manage_panel:member_group_list')

    all_members = Member.objects.filter(membership_status='active').order_by('last_name', 'first_name')
    selected_ids = set(group.members.values_list('pk', flat=True)) if group else set()
    return render(request, 'manage_panel/member_groups/form.html', {
        'group': group,
        'all_members': all_members,
        'selected_ids': selected_ids,
    })


@officer_required
@require_POST
def member_group_delete(request, pk):
    group = get_object_or_404(MemberGroup, pk=pk)
    name = group.name
    group.delete()
    messages.success(request, f'Group "{name}" deleted.')
    return redirect('manage_panel:member_group_list')


# ── Equipment ──────────────────────────────────────────────────────────────────

@officer_required
def equipment_list(request):
    items = EquipmentItem.objects.all()
    return render(request, 'manage_panel/equipment/list.html', {'items': items})


@officer_required
def equipment_form(request, pk=None):
    item = get_object_or_404(EquipmentItem, pk=pk) if pk else None
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        if not name:
            messages.error(request, 'Equipment name is required.')
        else:
            if item is None:
                item = EquipmentItem(name=name)
            else:
                item.name = name
            item.description = request.POST.get('description', '').strip()
            item.is_active = bool(request.POST.get('is_active'))
            if request.POST.get('clear_photo') == '1' and item.photo:
                item.photo.delete(save=False)
                item.photo = None
            if request.FILES.get('photo'):
                item.photo = request.FILES['photo']
            item.save()
            messages.success(request, f'Equipment "{item.name}" saved.')
            return redirect('manage_panel:equipment_list')
    return render(request, 'manage_panel/equipment/form.html', {'item': item})


@officer_required
@require_POST
def equipment_delete(request, pk):
    item = get_object_or_404(EquipmentItem, pk=pk)
    name = item.name
    item.delete()
    messages.success(request, f'Equipment "{name}" deleted.')
    return redirect('manage_panel:equipment_list')


# ── Events ─────────────────────────────────────────────────────────────────────

@officer_required
def event_list(request):
    """Officer view: upcoming + past events."""
    from django.utils import timezone as _tz
    now = _tz.now()
    upcoming = Event.objects.filter(ends_at__gte=now).select_related('equipment', 'location_trail', 'target_group').prefetch_related('assignees')
    past = Event.objects.filter(ends_at__lt=now).select_related('equipment').prefetch_related('assignees')[:30]
    return render(request, 'manage_panel/events/list.html', {
        'upcoming': upcoming,
        'past': past,
    })


def _parse_dt(value):
    """Parse the datetime-local HTML input format into a timezone-aware datetime."""
    from django.utils import timezone as _tz
    import datetime as _dt
    if not value:
        return None
    try:
        # datetime-local gives 'YYYY-MM-DDTHH:MM'
        naive = _dt.datetime.fromisoformat(value)
    except ValueError:
        return None
    if _tz.is_naive(naive):
        return _tz.make_aware(naive)
    return naive


@officer_required
def event_form(request, pk=None):
    from accounts.models import MemberGroup
    event = get_object_or_404(Event, pk=pk) if pk else None

    # ?lat=&lng= prefill from "click map → create here" flow (new events only)
    prefill_lat = prefill_lng = None
    if event is None and request.method == 'GET':
        try:
            if request.GET.get('lat'): prefill_lat = float(request.GET['lat'])
            if request.GET.get('lng'): prefill_lng = float(request.GET['lng'])
        except (ValueError, TypeError):
            prefill_lat = prefill_lng = None

    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        starts_at = _parse_dt(request.POST.get('starts_at'))
        ends_at   = _parse_dt(request.POST.get('ends_at'))

        if not title:
            messages.error(request, 'Title is required.')
        elif not starts_at or not ends_at:
            messages.error(request, 'Start and end times are required.')
        elif ends_at <= starts_at:
            messages.error(request, 'End time must be after start time.')
        else:
            if event is None:
                event = Event(created_by=request.user)
            event.title = title
            event.kind = request.POST.get('kind', 'work')
            event.description = request.POST.get('description', '').strip()
            event.starts_at = starts_at
            event.ends_at   = ends_at
            event.status     = request.POST.get('status', 'open')
            event.visibility = request.POST.get('visibility', 'members')
            event.location_text = request.POST.get('location_text', '').strip()

            trail_id = request.POST.get('location_trail') or ''
            event.location_trail_id = int(trail_id) if trail_id.isdigit() else None
            equip_id = request.POST.get('equipment') or ''
            event.equipment_id = int(equip_id) if equip_id.isdigit() else None
            group_id = request.POST.get('target_group') or ''
            event.target_group_id = int(group_id) if group_id.isdigit() else None

            try:
                event.location_lat = float(request.POST.get('location_lat')) if request.POST.get('location_lat') else None
                event.location_lng = float(request.POST.get('location_lng')) if request.POST.get('location_lng') else None
            except (ValueError, TypeError):
                event.location_lat = event.location_lng = None

            max_v = request.POST.get('max_volunteers', '').strip()
            event.max_volunteers = int(max_v) if max_v.isdigit() else None

            # Recurrence — only expand on CREATE, not edit
            recurrence = request.POST.get('recurrence', 'none')
            recurrence_count_raw = request.POST.get('recurrence_count', '').strip()
            # Sensible per-kind defaults when count is blank
            DEFAULT_COUNTS = {'daily': 30, 'weekly': 26, 'biweekly': 13, 'monthly': 12}
            try:
                if recurrence_count_raw:
                    recurrence_count = int(recurrence_count_raw)
                elif recurrence != 'none':
                    recurrence_count = DEFAULT_COUNTS.get(recurrence, 1)
                else:
                    recurrence_count = 1
            except ValueError:
                recurrence_count = DEFAULT_COUNTS.get(recurrence, 1) if recurrence != 'none' else 1
            recurrence_count = max(1, min(104, recurrence_count))   # 2-year safety cap

            is_new = event.pk is None
            event.recurrence = recurrence
            event.recurrence_count = recurrence_count if recurrence != 'none' else None
            event.save()

            if is_new and recurrence != 'none' and recurrence_count > 1:
                import uuid as _uuid
                import datetime as _dt
                group_id = _uuid.uuid4()
                event.recurrence_group = group_id
                event.save(update_fields=['recurrence_group'])
                delta_map = {
                    'daily':    _dt.timedelta(days=1),
                    'weekly':   _dt.timedelta(weeks=1),
                    'biweekly': _dt.timedelta(weeks=2),
                }
                for i in range(1, recurrence_count):
                    if recurrence == 'monthly':
                        # add i months (approximate via 30.44 days/month for simplicity;
                        # exact month math has edge cases like Feb 31)
                        offset = _dt.timedelta(days=int(round(30.44 * i)))
                    else:
                        offset = delta_map[recurrence] * i
                    Event.objects.create(
                        title=event.title, kind=event.kind, description=event.description,
                        starts_at=event.starts_at + offset, ends_at=event.ends_at + offset,
                        location_text=event.location_text,
                        location_trail_id=event.location_trail_id,
                        location_lat=event.location_lat, location_lng=event.location_lng,
                        equipment_id=event.equipment_id,
                        status=event.status, visibility=event.visibility,
                        max_volunteers=event.max_volunteers,
                        target_group_id=event.target_group_id,
                        created_by=event.created_by,
                        recurrence='none', recurrence_group=group_id,
                    )
                messages.success(request, f'Event "{event.title}" saved with {recurrence_count} occurrences.')
            else:
                messages.success(request, f'Event "{event.title}" saved.')
            return redirect('manage_panel:event_edit', pk=event.pk)

    trails = TrailSegment.objects.all()
    equipment_items = EquipmentItem.objects.filter(is_active=True)
    groups = MemberGroup.objects.all()
    candidates = event.rank_candidates() if event else []
    conflicts = list(event.equipment_conflicts()) if event else []

    return render(request, 'manage_panel/events/form.html', {
        'event': event,
        'trails': trails,
        'equipment_items': equipment_items,
        'groups': groups,
        'candidates': candidates,
        'conflicts': conflicts,
        'kind_choices': Event.KIND_CHOICES,
        'status_choices': Event.STATUS_CHOICES,
        'visibility_choices': Event.VISIBILITY_CHOICES,
        'prefill_lat': prefill_lat,
        'prefill_lng': prefill_lng,
    })


@officer_required
@require_POST
def event_delete(request, pk):
    event = get_object_or_404(Event, pk=pk)
    title = event.title
    event.delete()
    messages.success(request, f'Event "{title}" deleted.')
    return redirect('manage_panel:event_list')


@officer_required
@require_POST
def event_assign(request, pk):
    """Officer assigns a member to the event. Sends notification email."""
    event = get_object_or_404(Event, pk=pk)
    member_id = request.POST.get('member_id')
    member = get_object_or_404(Member, pk=member_id)
    if event.assignees.filter(pk=member.pk).exists():
        messages.info(request, f'{member.get_full_name()} is already on this event.')
    else:
        event.assignees.add(member)
        _notify_event_assignment(event, member, assigned_by=request.user)
        messages.success(request, f'{member.get_full_name()} added.')
    return redirect('manage_panel:event_edit', pk=pk)


@officer_required
@require_POST
def event_unassign(request, pk, member_pk):
    event = get_object_or_404(Event, pk=pk)
    event.assignees.remove(member_pk)
    messages.success(request, 'Member removed.')
    return redirect('manage_panel:event_edit', pk=pk)


def _notify_event_assignment(event, member, assigned_by=None):
    """Email a member that they've been added to an event."""
    from core.email import send_email as _send_email, _tmpl_override
    event_url = f"{getattr(settings, 'SITE_URL', '').rstrip('/')}/events/{event.pk}/"
    try:
        _send_email(
            subject=f'You\'ve been added to: {event.title}',
            to=member.email,
            template='event_assignment',
            context={
                'member':      member,
                'event':       event,
                'event_url':   event_url,
                'assigned_by': assigned_by.get_full_name() if assigned_by else None,
                **_tmpl_override('template_member'),
            },
        )
    except Exception:
        pass


# ── Member photo submission queue ──────────────────────────────────────────────

@officer_required
def photo_queue(request):
    from core.models import MemberShare
    show = request.GET.get('show', 'pending')
    qs = MemberShare.objects.select_related('member', 'reviewed_by').all()
    if show in ('pending', 'approved', 'rejected'):
        qs = qs.filter(status=show)
    return render(request, 'manage_panel/photo_queue.html', {
        'shares': qs[:100],
        'show': show,
        'pending_count': MemberShare.objects.filter(status='pending').count(),
    })


@officer_required
@require_POST
def photo_review(request, pk):
    from core.models import MemberShare, AnnouncementImage, TrailCondition, TrailConditionImage
    from django.utils import timezone as _tz
    share = get_object_or_404(MemberShare, pk=pk)
    decision = request.POST.get('decision')
    note = (request.POST.get('note') or '').strip()[:300]
    share.reviewed_by = request.user
    share.reviewed_at = _tz.now()
    share.review_note = note

    if decision == 'approve':
        # Approval path: create a TrailCondition (default kind for member shares
        # on the trail) and attach the photo as a TrailConditionImage. This puts
        # the photo on the public map and the conditions list.
        title = share.caption[:120] if share.caption else f'Photo from {share.member.get_short_name() if share.member else "member"}'
        cond = TrailCondition.objects.create(
            title=title, status='open', body=share.caption or '',
            visibility='public', lat=share.lat, lng=share.lng,
        )
        # Move the uploaded file to a TrailConditionImage row (re-open the file)
        share.image.open('rb')
        tci = TrailConditionImage(condition=cond, caption=share.caption[:200], lat=share.lat, lng=share.lng)
        tci.image.save(share.image.name.split('/')[-1], share.image, save=True)
        share.image.close()
        share.status = 'approved'
        share.save()
        messages.success(request, f'Approved — published as "{title}".')
    elif decision == 'reject':
        share.status = 'rejected'
        share.save()
        messages.info(request, 'Rejected.')
    return redirect('manage_panel:photo_queue')


@officer_required
@require_POST
def photo_delete(request, pk):
    from core.models import MemberShare
    share = get_object_or_404(MemberShare, pk=pk)
    if share.image:
        share.image.delete(save=False)
    share.delete()
    messages.success(request, 'Removed.')
    return redirect('manage_panel:photo_queue')
