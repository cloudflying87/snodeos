from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import models
from .models import ClubStats, Officer, Sponsor, TrailWorkLog, Announcement, TrailCondition
from .forms import ContactForm
from .email import notify_contact_message


def home(request):
    stats = ClubStats.objects.first()
    officers = Officer.objects.exclude(title='Director')
    sponsors = Sponsor.objects.filter(is_active=True)
    announcements = Announcement.objects.filter(
        visibility__in=['public', 'both']
    ).order_by('-is_pinned', '-created_at')[:5]
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

@login_required
def trail_work(request):
    logs = TrailWorkLog.objects.prefetch_related('images').all()
    return render(request, 'core/trail_work.html', {'logs': logs})


def trail_conditions(request):
    conditions = TrailCondition.objects.filter(
        visibility__in=['public', 'both']
    ).order_by('-is_pinned', '-created_at')[:20]
    return render(request, 'core/trail_conditions.html', {'conditions': conditions})


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
