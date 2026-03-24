from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib import messages
from django.views.generic import TemplateView
from django.utils import timezone
from .forms import CustomUserCreationForm


class HomeView(TemplateView):
    template_name = 'home.html'


def register(request):
    """User registration view."""
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Registration successful!')
            return redirect('dashboard')
    else:
        form = CustomUserCreationForm()
    return render(request, 'registration/register.html', {'form': form})


def dashboard(request):
    """Dashboard view based on user role."""
    if not request.user.is_authenticated:
        return redirect('login')

    if request.user.is_institution:
        return redirect('verification:pending_verifications')
    elif request.user.is_company:
        return redirect('verification:request_verification')
    else:
        return redirect('documents:document_list')

    return render(request, 'dashboard.html')


def status_page(request):
    """Public status page."""
    return render(request, 'status.html', {
        'last_update': timezone.now().strftime('%Y-%m-%d %H:%M:%S')
    })
