from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views.generic import ListView, CreateView, DetailView, DeleteView
from django.urls import reverse_lazy
from django.utils import timezone
from .models import Document
from .forms import DocumentUploadForm


class DocumentListView(LoginRequiredMixin, ListView):
    """List all documents for the current user."""
    model = Document
    template_name = 'documents/document_list.html'
    context_object_name = 'documents'

    def get_queryset(self):
        return Document.objects.filter(uploaded_by=self.request.user)


class DocumentUploadView(LoginRequiredMixin, CreateView):
    """Upload a new document."""
    model = Document
    form_class = DocumentUploadForm
    template_name = 'documents/document_upload.html'
    success_url = reverse_lazy('documents:document_list')

    def form_valid(self, form):
        form.instance.uploaded_by = self.request.user
        messages.success(self.request, 'Document uploaded successfully!')
        return super().form_valid(form)


class DocumentDetailView(LoginRequiredMixin, DetailView):
    """View document details."""
    model = Document
    template_name = 'documents/document_detail.html'
    context_object_name = 'document'

    def get_queryset(self):
        return Document.objects.filter(uploaded_by=self.request.user)


class DocumentDeleteView(LoginRequiredMixin, DeleteView):
    """Delete a document."""
    model = Document
    template_name = 'documents/document_delete.html'
    success_url = reverse_lazy('documents:document_list')

    def get_queryset(self):
        return Document.objects.filter(uploaded_by=self.request.user)


def refresh_verification_id(request, pk):
    """Refresh the verification ID for a document."""
    document = get_object_or_404(Document, pk=pk, uploaded_by=request.user)

    if document.verification_status != 'verified':
        messages.error(request, 'Only verified documents can have a verification ID.')
        return redirect('documents:document_detail', pk=pk)

    # Generate new verification ID
    new_id = document.generate_verification_id()
    messages.success(request, f'Verification ID refreshed! New ID: {new_id}')

    return redirect('documents:document_detail', pk=pk)
