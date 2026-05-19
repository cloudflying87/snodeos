from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.conf import settings
from core.models import ClubStats, Officer, OfficerTitle, Sponsor, Announcement, TrailWorkLog, TrailWorkImage, ContactMessage, SiteSettings
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
        if not (request.user.is_officer or request.user.is_staff):
            messages.error(request, 'Officer access required.')
            return redirect('core:home')
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
    import urllib.request, urllib.error, json
    cfg = SiteSettings.get()
    if cfg.facebook_integration != 'zapier' or not cfg.zapier_webhook_url:
        return
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
            messages.success(request, 'Announcement posted.')
            return redirect('manage_panel:announcement_list')
    else:
        form = AnnouncementForm()
    return render(request, 'manage_panel/announcements/form.html', {'form': form, 'action': 'New'})


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
                    membership_status=(row.get('membership_status') or row.get('Status') or 'active').strip().lower(),
                    membership_year=int(row['membership_year']) if (row.get('membership_year') or '').strip().isdigit() else None,
                )
                created += 1
            except Exception as e:
                errors += 1
                error_rows.append(f'Row {i} ({email}): {e}')

        results = {'created': created, 'skipped': skipped, 'errors': errors, 'error_rows': error_rows}

    return render(request, 'manage_panel/member_import.html', {'results': results})


# ── Facebook Integration ───────────────────────────────────────────────────────

@officer_required
def facebook_settings(request):
    cfg = SiteSettings.get()
    if request.method == 'POST':
        cfg.facebook_integration = request.POST.get('facebook_integration', 'none')
        cfg.facebook_page_url    = request.POST.get('facebook_page_url', '').strip()
        cfg.zapier_webhook_url   = request.POST.get('zapier_webhook_url', '').strip()
        cfg.save()
        messages.success(request, 'Facebook integration settings saved.')
        return redirect('manage_panel:facebook_settings')
    return render(request, 'manage_panel/facebook_settings.html', {'cfg': cfg})


# ── Email Blast ────────────────────────────────────────────────────────────────

@officer_required
def email_blast(request):
    from django.core.mail import send_mail
    recipients = Member.objects.filter(membership_status='active').values_list('email', flat=True)

    if request.method == 'POST':
        subject = request.POST.get('subject', '').strip()
        body = request.POST.get('body', '').strip()
        if not subject or not body:
            messages.error(request, 'Subject and body are required.')
        else:
            sent = 0
            failed = 0
            for email in recipients:
                try:
                    send_mail(
                        subject,
                        body,
                        settings.DEFAULT_FROM_EMAIL,
                        [email],
                        fail_silently=False,
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
    })


# ── Email Settings ─────────────────────────────────────────────────────────────

@officer_required
def email_settings(request):
    if request.method == 'POST' and 'send_test' in request.POST:
        recipient = request.POST.get('test_recipient', '').strip() or request.user.email
        try:
            send_test_email(recipient)
            messages.success(request, f'Test email sent to {recipient}. Check your inbox (and spam folder).')
        except Exception as exc:
            messages.error(request, f'Failed to send test email: {exc}')
        return redirect('manage_panel:email_settings')

    config = {
        'backend': settings.EMAIL_BACKEND,
        'host': settings.EMAIL_HOST or '(not set)',
        'port': settings.EMAIL_PORT,
        'use_tls': settings.EMAIL_USE_TLS,
        'user': settings.EMAIL_HOST_USER or '(not set)',
        'from_email': settings.DEFAULT_FROM_EMAIL,
        'notification_email': getattr(settings, 'NOTIFICATION_EMAIL', '') or '(not set)',
        'is_console': 'console' in settings.EMAIL_BACKEND,
        'is_smtp': 'smtp' in settings.EMAIL_BACKEND,
    }
    return render(request, 'manage_panel/email_settings.html', {'config': config})
