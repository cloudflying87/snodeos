from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import models
from django.http import JsonResponse
from django.urls import reverse
from .models import (
    ClubStats, Officer, Sponsor, TrailWorkLog, Announcement, TrailCondition,
    AnnouncementImage, TrailConditionImage, TrailWorkImage, TrailSegment,
    Event,
)
from .forms import ContactForm
from .email import notify_contact_message
from .throttle import throttle, get_client_ip


def home(request):
    stats = ClubStats.objects.first()
    officers = Officer.objects.exclude(title='Director')
    sponsors = Sponsor.objects.filter(is_active=True)
    announcements = Announcement.objects.filter(
        visibility__in=['public', 'both']
    ).prefetch_related('images').order_by('-is_pinned', '-created_at')[:5]
    context = {
        'stats': stats,
        'officers': officers,
        'sponsors': sponsors,
        'announcements': announcements,
    }
    return render(request, 'core/home.html', context)


def about(request):
    officers = Officer.objects.exclude(title='Director')
    directors = Officer.objects.filter(title='Director')
    return render(request, 'core/about.html', {'officers': officers, 'directors': directors})


def contact(request):
    if request.method == 'POST':
        # 5 submissions per IP per hour
        if not throttle(f'contact:{get_client_ip(request)}', max_count=5, window_seconds=3600):
            messages.error(request, "You've submitted several messages recently. Please wait a bit before sending another.")
            return redirect('core:contact')
        form = ContactForm(request.POST)
        if form.is_valid():
            contact_msg = form.save()
            notify_contact_message(contact_msg)
            # Auto-reply to the person who submitted
            from core.email import send_email as _send_email, _tmpl_override
            _send_email(
                subject='We received your message — Brainerd Snodeos',
                to=contact_msg.email,
                template='contact_reply',
                context={'msg': contact_msg, **_tmpl_override('template_contact_reply')},
            )
            messages.success(request, 'Your message has been sent! We will get back to you soon.')
            return redirect('core:contact')
    else:
        form = ContactForm()
    contact_officers = Officer.objects.exclude(title='Director').filter(
        models.Q(email__gt='') | models.Q(phone__gt='')
    )
    return render(request, 'core/contact.html', {'form': form, 'contact_officers': contact_officers})


from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404

def trail_work(request):
    """Legacy URL — the trail work list now lives on /map/. Permanent redirect."""
    from django.http import HttpResponsePermanentRedirect
    return HttpResponsePermanentRedirect(reverse('core:map') + '#work')


def trail_conditions(request):
    """Legacy URL — the trail conditions list now lives on /map/. Permanent redirect."""
    from django.http import HttpResponsePermanentRedirect
    return HttpResponsePermanentRedirect(reverse('core:map') + '#conditions')


def trail_condition_detail(request, pk):
    condition = get_object_or_404(TrailCondition, pk=pk)
    if not condition.is_public and not request.user.is_authenticated:
        from django.contrib.auth.views import redirect_to_login
        return redirect_to_login(request.get_full_path())
    return render(request, 'core/trail_condition_detail.html', {'condition': condition})


def announcement_detail(request, pk):
    ann = get_object_or_404(Announcement, pk=pk)
    # Members-only announcements require login
    if not ann.is_public and not request.user.is_authenticated:
        from django.contrib.auth.views import redirect_to_login
        return redirect_to_login(request.get_full_path())
    return render(request, 'core/announcement_detail.html', {'ann': ann})


def map_view(request):
    """Map-centric page that combines the interactive trail map with the
    most-recent trail conditions and (for members) recent trail work."""
    is_member = request.user.is_authenticated
    cond_qs = TrailCondition.objects.prefetch_related('images').order_by('-is_pinned', '-created_at')
    if not is_member:
        cond_qs = cond_qs.filter(visibility__in=['public', 'both'])
    conditions = cond_qs[:8]
    work_logs = TrailWorkLog.objects.prefetch_related('images').all()[:6] if is_member else []
    return render(request, 'core/map.html', {
        'conditions': conditions,
        'work_logs':  work_logs,
    })


def map_data(request):
    """JSON endpoint feeding the map page. Returns GeoJSON-shaped data for
    trails (LineStrings) and photos (Points). Respects visibility rules."""
    is_member = request.user.is_authenticated

    # ── Trail segments ─────────────────────────────────────────────────────
    seg_qs = TrailSegment.objects.all()
    if not is_member:
        seg_qs = seg_qs.filter(visibility__in=['public', 'both'])
    trails = []
    for seg in seg_qs:
        if not seg.geometry:
            continue
        trails.append({
            'id':         seg.pk,
            'name':       seg.name,
            'description': seg.description,
            'status':     seg.status,
            'status_label': seg.get_status_display(),
            'difficulty': seg.get_difficulty_display(),
            'visibility': seg.visibility,
            'color':      seg.effective_color,
            'groomed_at': seg.groomed_at.isoformat() if seg.groomed_at else None,
            # Leaflet wants [lat, lng] pairs; this matches what's stored
            'geometry':   seg.geometry,
            'gpx_url':    reverse('core:trail_segment_gpx', args=[seg.pk]),
        })

    # ── Geotagged photos ───────────────────────────────────────────────────
    photos = []

    def _add_photo(img, kind, parent_url, parent_label, visibility):
        if not img.has_location:
            return
        if visibility == 'members' and not is_member:
            return
        photos.append({
            'lat':           float(img.lat),
            'lng':           float(img.lng),
            'image_url':     img.image.url,
            'caption':       img.caption,
            'kind':          kind,
            'parent_label':  parent_label,
            'parent_url':    parent_url,
            'uploaded_at':   img.uploaded_at.isoformat(),
        })

    for img in AnnouncementImage.objects.select_related('announcement').filter(lat__isnull=False):
        ann = img.announcement
        _add_photo(img, 'announcement',
                   reverse('core:announcement_detail', args=[ann.pk]),
                   ann.title, ann.visibility)

    for img in TrailConditionImage.objects.select_related('condition').filter(lat__isnull=False):
        c = img.condition
        _add_photo(img, 'trail_condition',
                   reverse('core:trail_condition_detail', args=[c.pk]),
                   c.title, c.visibility)

    # Trail conditions placed directly via map-click (no photo, has lat/lng on the model)
    tc_qs = TrailCondition.objects.filter(lat__isnull=False, lng__isnull=False)
    if not is_member:
        tc_qs = tc_qs.filter(visibility__in=['public', 'both'])
    for c in tc_qs:
        photos.append({
            'lat':           float(c.lat),
            'lng':           float(c.lng),
            'image_url':     '',
            'caption':       c.body[:160] if c.body else '',
            'kind':          'trail_condition',
            'parent_label':  c.title,
            'parent_url':    reverse('core:trail_condition_detail', args=[c.pk]),
            'uploaded_at':   c.created_at.isoformat(),
        })

    # Trail work is members-only by site convention
    if is_member:
        for img in TrailWorkImage.objects.select_related('log').filter(lat__isnull=False):
            log = img.log
            _add_photo(img, 'trail_work', '#', log.title, 'members')

    return JsonResponse({'trails': trails, 'photos': photos})


def trail_segment_gpx(request, pk):
    """Export a TrailSegment as a .gpx file for import into Polaris Off Road,
    OnX, Gaia, Garmin, etc."""
    from django.http import HttpResponse
    seg = get_object_or_404(TrailSegment, pk=pk)
    if not seg.is_public and not request.user.is_authenticated:
        from django.contrib.auth.views import redirect_to_login
        return redirect_to_login(request.get_full_path())

    # Minimal valid GPX 1.1 — a single <trk> with one <trkseg>
    points = '\n'.join(
        f'      <trkpt lat="{lat}" lon="{lng}"></trkpt>'
        for (lat, lng) in (seg.geometry or [])
    )
    desc = (seg.description or '').replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    name = (seg.name or '').replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    gpx = f'''<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1" creator="SnoDeos"
     xmlns="http://www.topografix.com/GPX/1/1">
  <metadata>
    <name>{name}</name>
    <desc>{desc}</desc>
  </metadata>
  <trk>
    <name>{name}</name>
    <trkseg>
{points}
    </trkseg>
  </trk>
</gpx>
'''
    resp = HttpResponse(gpx, content_type='application/gpx+xml')
    safe_name = ''.join(ch if ch.isalnum() else '_' for ch in seg.name)[:60] or f'trail-{seg.pk}'
    resp['Content-Disposition'] = f'attachment; filename="{safe_name}.gpx"'
    return resp


def calendar_view(request):
    """Public calendar page (FullCalendar). Visibility-filtered events."""
    return render(request, 'core/calendar.html', {})


def calendar_data(request):
    """FullCalendar JSON feed. Accepts ?start=ISO&end=ISO."""
    from django.utils.dateparse import parse_datetime
    start = parse_datetime(request.GET.get('start', '')) if request.GET.get('start') else None
    end   = parse_datetime(request.GET.get('end',   '')) if request.GET.get('end')   else None

    qs = Event.objects.all()
    if not request.user.is_authenticated:
        qs = qs.filter(visibility__in=['public', 'both'])
    if start: qs = qs.filter(ends_at__gte=start)
    if end:   qs = qs.filter(starts_at__lte=end)

    events = []
    for e in qs.select_related('equipment', 'location_trail')[:500]:
        events.append({
            'id':    e.pk,
            'title': e.title,
            'start': e.starts_at.isoformat(),
            'end':   e.ends_at.isoformat(),
            'url':   f'/events/{e.pk}/',
            'color': e.effective_color,
            'extendedProps': {
                'kind':     e.get_kind_display(),
                'status':   e.get_status_display(),
                'location': e.location_label,
                'assigned': e.assignees.count(),
                'max':      e.max_volunteers,
            },
        })
    return JsonResponse(events, safe=False)


def event_detail(request, pk):
    event = get_object_or_404(Event, pk=pk)
    if not event.is_public and not request.user.is_authenticated:
        from django.contrib.auth.views import redirect_to_login
        return redirect_to_login(request.get_full_path())
    is_assigned = request.user.is_authenticated and event.assignees.filter(pk=request.user.pk).exists()
    return render(request, 'core/event_detail.html', {
        'event': event,
        'is_assigned': is_assigned,
    })


@login_required
def event_signup(request, pk):
    """Member self-signup. POST only."""
    if request.method != 'POST':
        return redirect('core:event_detail', pk=pk)
    event = get_object_or_404(Event, pk=pk)
    if not event.is_member_visible:
        messages.error(request, 'You cannot sign up for this event.')
        return redirect('core:event_detail', pk=pk)
    if event.status != 'open':
        messages.error(request, 'This event is not open for signups.')
    elif event.is_full:
        messages.error(request, 'This event is already full.')
    elif event.assignees.filter(pk=request.user.pk).exists():
        messages.info(request, "You're already signed up.")
    else:
        event.assignees.add(request.user)
        messages.success(request, f"You're signed up for {event.title}.")
        # Notify the creator (if any) that someone signed up
        if event.created_by_id and event.created_by_id != request.user.pk:
            from .email import send_email as _send_email
            try:
                _send_email(
                    subject=f'{request.user.get_full_name()} signed up for: {event.title}',
                    to=event.created_by.email,
                    template='event_signup',
                    context={'event': event, 'member': request.user},
                )
            except Exception:
                pass
    return redirect('core:event_detail', pk=pk)


@login_required
def event_withdraw(request, pk):
    """Member removes themselves from an event."""
    if request.method != 'POST':
        return redirect('core:event_detail', pk=pk)
    event = get_object_or_404(Event, pk=pk)
    if event.assignees.filter(pk=request.user.pk).exists():
        event.assignees.remove(request.user)
        messages.info(request, f"You've been removed from {event.title}.")
    return redirect('core:event_detail', pk=pk)


# ── Inbox / Internal Messaging ─────────────────────────────────────────────────

@login_required
def inbox(request):
    """All conversations the current user participates in."""
    convs = (request.user.conversations
             .prefetch_related('messages', 'participants')
             .order_by('-last_activity'))
    return render(request, 'core/inbox.html', {'conversations': convs})


@login_required
def conversation_detail(request, pk):
    from .models import Conversation, InternalMessage
    conv = get_object_or_404(Conversation, pk=pk, participants=request.user)
    if request.method == 'POST':
        body = (request.POST.get('body') or '').strip()
        if body:
            msg = InternalMessage.objects.create(conversation=conv, sender=request.user, body=body)
            msg.read_by.add(request.user)
            from django.utils import timezone as _tz
            conv.last_activity = _tz.now()
            conv.save(update_fields=['last_activity'])
            _notify_message_recipients(conv, msg, exclude_user=request.user)
            return redirect('core:conversation_detail', pk=pk)

    msgs = conv.messages.select_related('sender').all()
    # Mark unread messages as read by this user
    from django.db.models import Q as _Q
    unread = msgs.exclude(read_by=request.user)
    for m in unread:
        m.read_by.add(request.user)

    return render(request, 'core/conversation_detail.html', {
        'conversation': conv,
        'messages_list': msgs,
        'others': conv.participants.exclude(pk=request.user.pk),
    })


@login_required
def inbox_compose(request):
    """Send a new message to one or more members, or a MemberGroup."""
    from .models import Conversation, InternalMessage
    from accounts.models import Member, MemberGroup
    if request.method == 'POST':
        subject = (request.POST.get('subject') or '').strip()
        body    = (request.POST.get('body') or '').strip()
        recipient_ids = request.POST.getlist('recipient_ids')
        group_id = request.POST.get('group_id') or ''

        if not subject or not body:
            messages.error(request, 'Subject and body are required.')
            return redirect('core:inbox_compose')

        # Resolve recipients
        recipients = set()
        for rid in recipient_ids:
            if rid.isdigit():
                m = Member.objects.filter(pk=int(rid)).first()
                if m: recipients.add(m)
        if group_id.isdigit():
            grp = MemberGroup.objects.filter(pk=int(group_id)).first()
            if grp:
                # Only officers can blast a whole group
                if request.user.is_officer or request.user.is_site_admin or request.user.is_staff:
                    for m in grp.members.filter(membership_status='active'):
                        recipients.add(m)
                else:
                    messages.error(request, 'Only officers can send to a whole group.')
                    return redirect('core:inbox_compose')

        if not recipients:
            messages.error(request, 'Pick at least one recipient.')
            return redirect('core:inbox_compose')

        conv = Conversation.objects.create(subject=subject)
        conv.participants.add(request.user, *recipients)
        msg = InternalMessage.objects.create(conversation=conv, sender=request.user, body=body)
        msg.read_by.add(request.user)
        _notify_message_recipients(conv, msg, exclude_user=request.user)
        messages.success(request, f'Message sent to {len(recipients)} member{"" if len(recipients)==1 else "s"}.')
        return redirect('core:conversation_detail', pk=conv.pk)

    members = Member.objects.filter(membership_status='active').exclude(pk=request.user.pk).order_by('last_name', 'first_name')
    can_blast_group = request.user.is_officer or request.user.is_site_admin or request.user.is_staff
    groups = MemberGroup.objects.all() if can_blast_group else []
    return render(request, 'core/inbox_compose.html', {
        'members':         members,
        'groups':          groups,
        'can_blast_group': can_blast_group,
    })


def _notify_message_recipients(conversation, message, exclude_user=None):
    """Create Notification rows + send a notification email when a new message
    is sent. Best-effort — never raises."""
    from .notify import notify
    from .email import send_email as _send_email, _tmpl_override
    from django.conf import settings as _settings
    msg_url = f'/inbox/{conversation.pk}/'
    site_url = getattr(_settings, 'SITE_URL', '').rstrip('/')

    for member in conversation.participants.all():
        if exclude_user and member.pk == exclude_user.pk:
            continue
        notify(member, 'message', f'{message.sender.get_short_name() if message.sender else "Someone"}: {conversation.subject}', msg_url)
        try:
            _send_email(
                subject=f'New message: {conversation.subject}',
                to=member.email,
                template='internal_message',
                context={
                    'recipient':    member,
                    'sender':       message.sender,
                    'conversation': conversation,
                    'message':      message,
                    'inbox_url':    f'{site_url}{msg_url}',
                    **_tmpl_override('template_member'),
                },
            )
        except Exception:
            pass


# ── Notifications ──────────────────────────────────────────────────────────────

@login_required
def notifications_view(request):
    notifs = request.user.notifications.all()[:100]
    return render(request, 'core/notifications.html', {'notifs': notifs})


@login_required
def notification_open(request, pk):
    """Mark a notification read, then redirect to its target URL."""
    from .models import Notification
    notif = get_object_or_404(Notification, pk=pk, user=request.user)
    notif.is_read = True
    notif.save(update_fields=['is_read'])
    return redirect(notif.url or 'core:notifications')


@login_required
def notifications_mark_all_read(request):
    if request.method == 'POST':
        request.user.notifications.filter(is_read=False).update(is_read=True)
    return redirect('core:notifications')


# ── iCal feed ──────────────────────────────────────────────────────────────────

def _ical_response(events, calname):
    """Return events as RFC 5545 iCalendar text."""
    from django.http import HttpResponse
    import datetime as _dt
    def _fmt(dt):
        return dt.strftime('%Y%m%dT%H%M%SZ') if dt else ''
    lines = [
        'BEGIN:VCALENDAR',
        'VERSION:2.0',
        'PRODID:-//SnoDeos//Events//EN',
        f'X-WR-CALNAME:{calname}',
        'CALSCALE:GREGORIAN',
    ]
    for e in events:
        # UID needs to be stable per event
        uid = f'event-{e.pk}@snodeos'
        desc = (e.description or '').replace('\n', '\\n').replace(',', '\\,').replace(';', '\;')
        title = (e.title or '').replace(',', '\\,').replace(';', '\;')
        loc = (e.location_label or '').replace(',', '\\,').replace(';', '\;')
        lines += [
            'BEGIN:VEVENT',
            f'UID:{uid}',
            f'DTSTAMP:{_fmt(e.created_at.astimezone(_dt.timezone.utc) if e.created_at else _dt.datetime.now(_dt.timezone.utc))}',
            f'DTSTART:{_fmt(e.starts_at.astimezone(_dt.timezone.utc))}',
            f'DTEND:{_fmt(e.ends_at.astimezone(_dt.timezone.utc))}',
            f'SUMMARY:{title}',
        ]
        if desc:
            lines.append(f'DESCRIPTION:{desc}')
        if loc:
            lines.append(f'LOCATION:{loc}')
        lines.append('END:VEVENT')
    lines.append('END:VCALENDAR')
    body = '\r\n'.join(lines) + '\r\n'
    resp = HttpResponse(body, content_type='text/calendar; charset=utf-8')
    resp['Content-Disposition'] = f'inline; filename="{calname.lower().replace(" ", "-")}.ics"'
    return resp


def calendar_ics(request):
    """Public iCal feed — public/both events only. No auth required so members
    can subscribe in Google Calendar, Apple Calendar, etc."""
    qs = Event.objects.filter(visibility__in=['public', 'both']).exclude(status='cancelled').order_by('starts_at')
    return _ical_response(qs, 'Brainerd Snodeos')


@login_required
def members_calendar_ics(request):
    """Members-only iCal feed — includes members-only events. Requires login."""
    qs = Event.objects.exclude(status='cancelled').order_by('starts_at')
    return _ical_response(qs, 'Brainerd Snodeos (All)')


# ── Member photo submissions ───────────────────────────────────────────────────

@login_required
def share_photo(request):
    """Member-facing form to submit a photo for officer review."""
    from .models import MemberShare
    from .geo import extract_gps
    if request.method == 'POST' and request.FILES.get('image'):
        img = request.FILES['image']
        lat, lng = extract_gps(img)
        share = MemberShare.objects.create(
            member=request.user, image=img,
            caption=(request.POST.get('caption') or '').strip()[:300],
            lat=lat, lng=lng,
        )
        # Notify officers (active officers) via Notification
        from accounts.models import Member as _M
        from .notify import notify
        officers = _M.objects.filter(membership_status='active').filter(
            models.Q(is_officer=True) | models.Q(is_site_admin=True) | models.Q(is_staff=True)
        ).distinct()
        review_url = '/manage/photo-queue/'
        for o in officers:
            notify(o, 'photo_submission', f'{request.user.get_short_name()} shared a photo', review_url)
        messages.success(request, 'Thanks! Your photo is in the review queue. You\'ll see it on the map once an officer approves it.')
        return redirect('members:dashboard')
    return render(request, 'core/share_photo.html', {})
