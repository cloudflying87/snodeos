from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib import messages
from core.email import notify_new_application
from .forms import MembershipApplicationForm, MemberLoginForm


def register(request):
    if request.user.is_authenticated:
        return redirect('members:dashboard')
    if request.method == 'POST':
        form = MembershipApplicationForm(request.POST)
        if form.is_valid():
            member = form.save()
            notify_new_application(member)
            messages.success(request, 'Your application has been submitted! An officer will review it shortly.')
            return redirect('core:home')
    else:
        form = MembershipApplicationForm()
    return render(request, 'accounts/register.html', {'form': form})


def member_login(request):
    if request.user.is_authenticated:
        return redirect('members:dashboard')
    if request.method == 'POST':
        form = MemberLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            if user.membership_status == 'pending':
                messages.warning(request, 'Your membership application is still pending approval.')
                return redirect('core:home')
            login(request, user)
            return redirect('members:dashboard')
        else:
            messages.error(request, 'Invalid email or password.')
    else:
        form = MemberLoginForm(request)
    return render(request, 'accounts/login.html', {'form': form})


def member_logout(request):
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('core:home')
