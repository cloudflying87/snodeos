from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import models
from django.http import JsonResponse
from django.urls import reverse
from .models import (
    ClubStats, Officer, Sponsor, TrailWorkLog, Announcement, TrailCondition,
    AnnouncementImage, TrailConditionImage, TrailWorkImage, TrailSegment,
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
