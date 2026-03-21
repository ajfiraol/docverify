from django import forms
from .models import VerificationRequest, DocumentVerification
from documents.models import Document


class VerificationRequestForm(forms.ModelForm):
    """Form for requesting document verification."""

    class Meta:
        model = VerificationRequest
        fields = ['document', 'purpose']
        widgets = {
            'purpose': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Enter the purpose of verification...'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields['document'].queryset = Document.objects.filter(uploaded_by=user)


class VerificationForm(forms.ModelForm):
    """Form for institutions to verify documents."""

    class Meta:
        model = DocumentVerification
        fields = ['status', 'notes']
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Add verification notes...'}),
        }
