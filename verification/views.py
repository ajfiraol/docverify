from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views.generic import ListView, CreateView, FormView, DetailView
from django.urls import reverse_lazy
from .models import VerificationRequest, DocumentVerification
from .forms import VerificationRequestForm, VerificationForm
from documents.models import Document


class RequestVerificationView(LoginRequiredMixin, CreateView):
    """Company requests document verification."""
    model = VerificationRequest
    form_class = VerificationRequestForm
    template_name = 'verification/request_verification.html'
    success_url = reverse_lazy('verification:my_requests')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.requested_by = self.request.user
        messages.success(self.request, 'Verification request submitted!')
        return super().form_valid(form)


class MyVerificationRequestsView(LoginRequiredMixin, ListView):
    """List company's verification requests."""
    model = VerificationRequest
    template_name = 'verification/my_requests.html'
    context_object_name = 'requests'

    def get_queryset(self):
        return VerificationRequest.objects.filter(requested_by=self.request.user)


class PendingVerificationsView(LoginRequiredMixin, ListView):
    """Institution views pending verifications."""
    model = Document
    template_name = 'verification/pending_verifications.html'
    context_object_name = 'documents'

    def get_queryset(self):
        return Document.objects.filter(status='pending').order_by('-created_at')


class VerifyDocumentView(LoginRequiredMixin, FormView):
    """Institution verifies a document."""
    model = DocumentVerification
    form_class = VerificationForm
    template_name = 'verification/verify_document.html'

    def get_document(self):
        return get_object_or_404(Document, pk=self.kwargs['pk'])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['document'] = self.get_document()
        return context

    def form_valid(self, form):
        document = self.get_document()
        verification = form.save(commit=False)
        verification.document = document
        verification.verified_by = self.request.user
        verification.verification_type = 'institution'
        verification.save()

        # Update document status
        document.status = form.cleaned_data['status']
        document.verification_status = form.cleaned_data['status']

        # Generate verification ID when document is verified
        if form.cleaned_data['status'] == 'verified':
            document.generate_verification_id()

        document.save()

        messages.success(self.request, 'Document verified successfully!')
        return redirect('verification:pending_verifications')


class VerificationHistoryView(LoginRequiredMixin, ListView):
    """View verification history."""
    model = DocumentVerification
    template_name = 'verification/history.html'
    context_object_name = 'verifications'

    def get_queryset(self):
        return DocumentVerification.objects.filter(verified_by=self.request.user)


class DocumentVerificationListView(LoginRequiredMixin, ListView):
    """List all document verifications (for institutions)."""
    model = DocumentVerification
    template_name = 'verification/verification_list.html'
    context_object_name = 'verifications'

    def get_queryset(self):
        return DocumentVerification.objects.all().order_by('-verified_at')


class VerifyByIdView(FormView):
    """Anyone can verify document authenticity using verification ID."""
    template_name = 'verification/verify_by_id.html'
    form_class = None  # Will use a simple form defined in get

    def get_form_class(self):
        from django import forms
        class VerifyByIdForm(forms.Form):
            verification_id = forms.CharField(max_length=12, required=True, label='Verification ID')
        return VerifyByIdForm

    def form_valid(self, form):
        verification_id = form.cleaned_data['verification_id'].upper()
        document = Document.objects.filter(verification_id=verification_id).first()

        if not document:
            messages.error(self.request, 'Invalid verification ID. Please check and try again.')
            return self.form_invalid(form)

        if not document.is_verification_id_valid(verification_id):
            messages.error(self.request, 'Verification ID has expired. Please request a new one.')
            return self.form_invalid(form)

        # Valid - show document details
        return render(self.request, 'verification/verification_result.html', {
            'document': document,
            'verification_id': verification_id,
        })

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Verify Document Authenticity'
        return context
