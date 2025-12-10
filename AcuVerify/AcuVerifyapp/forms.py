"""
=============================================================================
AcuVerify Forms
=============================================================================
This module defines all Django forms used for data input and validation.
Includes forms for staff registration, student enrollment, stream assignment, 
login/authentication, and class management.
=============================================================================
"""

from django.contrib.auth.forms import UserCreationForm
from django import forms
from django.contrib.auth.models import User
from .models import Staff, Subject, Classes, Students, Streams


class StaffRegistrationForm(forms.ModelForm):
    """
    Form for registering a new staff member.
    
    Features:
    - Auto-creates common Kenyan curriculum subjects if missing
    - Subject checkboxes: allows staff to select their specializations
    - Gender radio buttons: M/F selection
    - Custom save() to properly set ManyToMany relationships
    
    KENYA_SUBJECTS: List of standard subjects taught in Kenyan schools.
    These are created in a "General" class if they don't exist.
    """
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
        Uses a generic "General" class to attach subjects if none are present.
        
        This is run on form init so subjects are always available in the dropdown.
        Uses bulk_create with ignore_conflicts=True to avoid duplicates.
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

    def save(self, commit=True):
        """
        Override save to properly handle ManyToMany field (subject_specialization).
        
        Process:
        1. Save the Staff instance (without committing ManyToMany)
        2. Save to DB if commit=True
        3. Explicitly set the ManyToMany relationships using set()
        
        This ensures only selected subjects are linked to the staff member.
        """
        staff = super().save(commit=False)
        if commit:
            staff.save()
            # Explicitly set M2M to the chosen subjects only
            staff.subject_specialization.set(self.cleaned_data.get('subject_specialization'))
        return staff

    # Subject specialization: staff can select multiple subjects they teach
    subject_specialization = forms.ModelMultipleChoiceField(
        queryset=Subject.objects.all(),
        widget=forms.CheckboxSelectMultiple(attrs={"class": "form-check-input me-2"}),
        required=False,
        help_text='Select one or more subjects this staff member specializes in.'
    )
    
    # Gender field: radio buttons (M/F)
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
    """
    Form for registering a new student.
    
    Fields: First/last name, email, address, phone, class, and stream enrollment.
    The student must be assigned to a class and stream during registration.
    """
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
    """
    Form for creating/editing a class.
    Allows admin to define a class name and its education level (Primary, JSS, SSS).
    """
    class Meta:
        model = Classes
        fields = ['class_name', 'education_level']
        labels = {
            'class_name': 'Class Name',
            'education_level': 'Education Level'
        }


class EmailForm(forms.Form):
    """
    First step of multi-step login form.
    User enters their email address to check if they exist in the system.
    """
    email = forms.EmailField(
        label='Email Address',
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter your email address'})
    )


class PasswordForm(forms.Form):
    """
    Second step of login for existing Django users.
    User who already has a password enters it for authentication.
    """
    password = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Enter your password'})
    )


class CreatePasswordForm(forms.Form):
    """
    Second step of login for new users (Staff/Students).
    New users who don't have a password yet create one here.
    
    Validation: Passwords must match and be at least 8 characters.
    """
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
        """
        Custom validation to ensure both password fields match.
        """
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')

        if password and password_confirm:
            if password != password_confirm:
                raise forms.ValidationError("Passwords do not match.")
        return cleaned_data        


class AssignStreamForm(forms.Form):
    """
    Form for assigning a stream/class and subjects to a teacher.
    
    Admin uses this form to:
    1. Select a staff member (teacher)
    2. Select a stream they will teach
    3. Select which subjects they will teach in that stream
    
    The subjects field is dynamically populated during __init__ to show only:
    - Subjects belonging to the selected stream's class
    - Subjects that match the teacher's specializations (subject_specialization)
    
    This ensures a teacher is only assigned subjects they are qualified to teach.
    """
    staff = forms.ModelChoiceField(
        queryset=Staff.objects.all(),
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Select Teacher'
    )
    stream = forms.ModelChoiceField(
        queryset=Streams.objects.all(),
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Select Stream/Class'
    )
    # Subjects: dynamically populated based on staff + stream selection
    subjects = forms.ModelMultipleChoiceField(
        queryset=Subject.objects.none(),  # Will be populated in __init__
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input me-2'}),
        label='Subjects to Teach'
    )

    def __init__(self, *args, **kwargs):
        """
        Dynamic form initialization.
        
        If form is bound (submitted), extracts staff_id and stream_id from POST data.
        Then populates the subjects field with the intersection of:
        - Subjects in the stream's class
        - Subjects the staff member specializes in
        
        This ensures we only show relevant subjects for assignment.
        """
        super().__init__(*args, **kwargs)
        data = None
        if args:
            # bound form — args[0] is the data dict (POST data)
            data = args[0]

        # Pre-populate staff and stream querysets with ordering
        staff_qs = Staff.objects.all().order_by('fname', 'lname')
        self.fields['staff'].queryset = staff_qs

        stream_qs = Streams.objects.select_related('class_id').all().order_by('class_id__class_name', 'stream_name')
        self.fields['stream'].queryset = stream_qs

        # If the form is bound and staff+stream were provided, limit subjects to the intersection
        # between the staff's specializations and the subjects for the selected stream's class.
        try:
            staff_id = int(data.get('staff')) if data and data.get('staff') else None
        except (ValueError, TypeError):
            staff_id = None
        try:
            stream_id = int(data.get('stream')) if data and data.get('stream') else None
        except (ValueError, TypeError):
            stream_id = None

        if staff_id and stream_id:
            try:
                staff = Staff.objects.get(id=staff_id)
                stream = Streams.objects.select_related('class_id').get(id=stream_id)
                # Subjects that belong to the stream's class AND are in staff specializations
                qs = Subject.objects.filter(
                    class_id=stream.class_id,
                    id__in=staff.subject_specialization.values_list('id', flat=True)
                ).order_by('subject_name')
                self.fields['subjects'].queryset = qs
            except (Staff.DoesNotExist, Streams.DoesNotExist):
                # If staff or stream doesn't exist, show no subjects
                self.fields['subjects'].queryset = Subject.objects.none()
        else:
            # Unbound form or missing selections — keep subjects empty to avoid showing irrelevant choices
            self.fields['subjects'].queryset = Subject.objects.none()