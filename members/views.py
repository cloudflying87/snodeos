from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q
from accounts.models import Member
from core.models import Announcement, TrailCondition, TrailWorkLog
from core.email import notify_application_approved
from .forms import MemberEditForm, MemberFilterForm, ProfileEditForm


def officer_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        if not (request.user.is_officer or request.user.is_staff):
            messages.error(request, 'You must be a club officer to access this area.')
            return redirect('core:home')
        return view_func(request, *args, **kwargs)
    return wrapper


@login_required
def dashboard(request):
    member = request.user
    announcements = Announcement.objects.filter(
        visibility__in=['members', 'both']
    ).prefetch_related('images').order_by('-is_pinned', '-created_at')[:6]
    trail_conditions = TrailCondition.objects.filter(
        visibility__in=['members', 'both']
    ).prefetch_related('images').order_by('-is_pinned', '-created_at')[:6]

    feed = []
    for a in announcements:
        img = a.images.first()
        feed.append({
            'kind': 'announcement',
            'badge': 'Announcement',
            'badge_class': 'bg-primary-subtle text-primary-emphasis',
            'icon': 'megaphone',
            'title': a.title,
            'snippet': a.body,
            'image': img.image.url if img else None,
            'date': a.created_at,
            'pinned': a.is_pinned,
            'url': f'/announcements/{a.pk}/',
        })
    for tc in trail_conditions:
        img = tc.images.first()
        feed.append({
            'kind': 'trail_condition',
            'badge': tc.get_status_display(),
            'badge_class': tc.status_badge_class,
            'icon': 'signpost-split',
            'title': tc.title,
            'snippet': tc.body,
            'image': img.image.url if img else None,
            'date': tc.created_at,
            'pinned': tc.is_pinned,
            'url': f'/trail-conditions/{tc.pk}/',
        })
    # Sort merged feed: pinned first, then by date desc; cap at 10
    feed.sort(key=lambda x: (not x['pinned'], -x['date'].timestamp()))
    feed = feed[:10]

    my_groups = member.groups_membership.all() if hasattr(member, 'groups_membership') else []

    context = {
        'member': member,
        'feed': feed,
        'my_groups': my_groups,
    }
    return render(request, 'members/dashboard.html', context)


@officer_required
def member_list(request):
    form = MemberFilterForm(request.GET)
    members = Member.objects.all()

    search = request.GET.get('search', '')
    status = request.GET.get('status', '')

    if search:
        members = members.filter(
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(email__icontains=search)
        )
    if status:
        members = members.filter(membership_status=status)

    context = {'members': members, 'form': form, 'search': search, 'status': status}
    return render(request, 'members/member_list.html', context)


@officer_required
def member_detail(request, pk):
    member = get_object_or_404(Member, pk=pk)
    return render(request, 'members/member_detail.html', {'member': member})


@officer_required
def member_edit(request, pk):
    member = get_object_or_404(Member, pk=pk)
    if request.method == 'POST':
        form = MemberEditForm(request.POST, request.FILES, instance=member)
        if form.is_valid():
            form.save()
            messages.success(request, f'{member.get_full_name()} has been updated.')
            return redirect('members:member_detail', pk=pk)
    else:
        form = MemberEditForm(instance=member)
    return render(request, 'members/member_edit.html', {'form': form, 'member': member})


@officer_required
def approve_member(request, pk):
    from core.audit import log_action
    member = get_object_or_404(Member, pk=pk)
    member.membership_status = 'active'
    member.date_approved = timezone.now().date()
    member.membership_year = timezone.now().year
    member.save()
    notify_application_approved(member)
    log_action(request.user, 'member_approve', target=member.get_full_name(), detail=f'Email: {member.email}')
    messages.success(request, f'{member.get_full_name()} has been approved as an active member.')
    return redirect('members:member_list')


@officer_required
def deactivate_member(request, pk):
    from core.audit import log_action
    member = get_object_or_404(Member, pk=pk)
    member.membership_status = 'inactive'
    member.save()
    log_action(request.user, 'member_deactivate', target=member.get_full_name(), detail=f'Email: {member.email}')
    messages.warning(request, f'{member.get_full_name()} has been deactivated.')
    return redirect('members:member_list')


@login_required
def profile_edit(request):
    if request.method == 'POST':
        form = ProfileEditForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated.')
            return redirect('members:dashboard')
    else:
        form = ProfileEditForm(instance=request.user)
    return render(request, 'members/profile_edit.html', {'form': form})


@officer_required
def pending_applications(request):
    pending = Member.objects.filter(membership_status='pending').order_by('date_applied')
    return render(request, 'members/pending.html', {'pending': pending})
