from django.contrib.auth.forms import UserCreationForm
from django import forms
from django.contrib.auth.models import User
from .models import Staff, Subject, Classes, Students, Streams


class StaffRegistrationForm(forms.ModelForm):
    # National Curriculum subjects commonly taught in Kenyan schools
    KENYA_SUBJECTS = [
        "Mathematics",
        "English",
        "Kiswahili",
        "Chemistry",
        "Biology",
        "Physics",
        "History and Government",
        "Geography",
        "CRE",
        "IRE",
        "HRE",
        "Business Studies",
        "Agriculture",
        "Computer Studies",
        "Home Science",
        "Music",
        "Art and Design",
        "French",
        "German",
        "Arabic",
        "Sign Language",
        "Physical Education",
        "Life Skills",
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._ensure_default_subjects()
        # Refresh queryset so the form shows the ensured subjects
        self.fields["subject_specialization"].queryset = Subject.objects.all().order_by("subject_name")

    def _ensure_default_subjects(self):
        """
        Make sure the common Kenyan subjects exist so the checkboxes appear.
        Uses a generic class bucket to attach subjects if none are present.
        """
        generic_class, _ = Classes.objects.get_or_create(class_name="General", defaults={"education_level": None})
        existing_names = set(
            Subject.objects.filter(subject_name__in=self.KENYA_SUBJECTS).values_list("subject_name", flat=True)
        )
        missing = [name for name in self.KENYA_SUBJECTS if name not in existing_names]
        Subject.objects.bulk_create(
            [Subject(subject_name=name, class_id=generic_class) for name in missing],
            ignore_conflicts=True,
        )

    subject_specialization = forms.ModelMultipleChoiceField(
        queryset=Subject.objects.all(),
        widget=forms.CheckboxSelectMultiple(attrs={"class": "form-check-input me-2"}),
        required=False,
        help_text='Select one or more subjects this staff member specializes in.'
    )
    gender = forms.ChoiceField(
        choices=[('M', 'Male'), ('F', 'Female')],
        widget=forms.RadioSelect(attrs={"class": "form-check-input me-2"}),
        required=True,
        label='Gender'
    )
    class Meta:
        model = Staff
        fields = ['fname', 'lname', 'email', 'gender', 'position', 'department', 'address', 'subject_specialization', 'phone_number']
        widgets = {
            'gender': forms.RadioSelect(attrs={"class": "form-check-input me-2"}),
        }
        
        labels = {
            'fname': 'First Name',
            'lname': 'Last Name',
            'email': 'Email Address',
            'position': 'Position',
            'department': 'Department',
            'address': 'Residential Address',
            'phone_number': 'Phone Number',
        }


class StudentRegistrationForm(forms.ModelForm):
    class Meta:
        model = Students
        fields = ['fname', 'lname', 'email', 'address', 'phone_number', 'class_id','stream_id']
        labels = {
            'fname': 'First Name',
            'lname': 'Last Name',
            'email': 'Email Address',
            'address': 'Residential Address',
            'phone_number': 'Phone Number',
            'class_id': 'Class Enrolled',
            'stream_id': 'Stream Enrolled'
        }      


class ClassForm(forms.ModelForm):
    class Meta:
        model = Classes
        fields = ['class_name', 'education_level']
        labels = {
            'class_name': 'Class Name',
            'education_level': 'Education Level'
        }


class EmailForm(forms.Form):
    email = forms.EmailField(
        label='Email Address',
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter your email address'})
    )


class PasswordForm(forms.Form):
    password = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Enter your password'})
    )


class CreatePasswordForm(forms.Form):
    password = forms.CharField(
        label='Create Password',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Create a password'}),
        min_length=8,
        help_text='Password must be at least 8 characters long.'
    )
    password_confirm = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm your password'})
    )

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')

        if password and password_confirm:
            if password != password_confirm:
                raise forms.ValidationError("Passwords do not match.")
        return cleaned_data        