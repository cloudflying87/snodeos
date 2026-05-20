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
