from django import forms
from .models import UserAccidentReport, Accident

# ----------------------------------
# Minimal form for witness/quick report
# ----------------------------------
class MinimalAccidentForm(forms.ModelForm):
    class Meta:
        model = Accident
        fields = ['description', 'localisation', 'latitude', 'longitude']
        widgets = {
            'description': forms.Textarea(attrs={
                'class': 'form-control', 
                'placeholder': 'Describe the accident', 
                'rows': 2
            }),
            'localisation': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Location'
            }),
            'latitude': forms.HiddenInput(),
            'longitude': forms.HiddenInput(),
        }

# ----------------------------------
# Shared base form (DO NOT use directly)
# ----------------------------------
class BaseAccidentForm(forms.ModelForm):
    class Meta:
        fields = [
            'reporter_name', 'reporter_phone', 'reporter_cin',
            'accident_datetime', 'localisation', 'latitude', 'longitude',
            'car_type', 'reason', 'description',
            'other_name', 'other_cin', 'other_phone',
            'guilty'
        ]
        widgets = {
            'reporter_name': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'Your Name'
            }),
            'reporter_phone': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'Your Phone Number'
            }),
            'reporter_cin': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'Your CIN'
            }),
            'accident_datetime': forms.DateTimeInput(attrs={
                'class': 'form-control', 'type': 'datetime-local'
            }),
            'localisation': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'Location'
            }),
            'latitude': forms.HiddenInput(),
            'longitude': forms.HiddenInput(),
            'car_type': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'Car Type'
            }),
            'reason': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Reason of Accident',
                'rows': 2
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Describe the accident',
                'rows': 2
            }),
            'other_name': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'Other Party Name'
            }),
            'other_cin': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'Other Party CIN'
            }),
            'other_phone': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'Other Party Phone'
            }),
            'guilty': forms.Select(attrs={'class': 'form-select'}),
        }

# ----------------------------------
# Witness / Passenger Report Form
# ----------------------------------
class UserAccidentReportForm(BaseAccidentForm):
    class Meta(BaseAccidentForm.Meta):
        model = UserAccidentReport

# ----------------------------------
# Main Accident Form
# ----------------------------------
class AccidentForm(BaseAccidentForm):
    class Meta(BaseAccidentForm.Meta):
        model = Accident
