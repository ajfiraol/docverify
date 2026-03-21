from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView
from accounts.models import User


class InstitutionListView(LoginRequiredMixin, ListView):
    """List all verified institutions."""
    model = User
    template_name = 'institutions/institution_list.html'
    context_object_name = 'institutions'

    def get_queryset(self):
        return User.objects.filter(role='institution', is_active=True).order_by('username')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Institutions'
        return context
