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
from .models import Staff, Subject, Classes, Students, Streams, AcademicYear


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
        fields = ['fname', 'lname', 'email', 'phone_number', 'date_of_birth', 'gender', 'position', 'department', 'address', 'subject_specialization']
        widgets = {
            'gender': forms.RadioSelect(attrs={"class": "form-check-input me-2"}),
            'date_of_birth': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'position': forms.TextInput(attrs={'class': 'form-control'}),
            'department': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
        
        labels = {
            'fname': 'First Name',
            'lname': 'Last Name',
            'email': 'Email Address',
            'position': 'Position',
            'department': 'Department',
            'address': 'Residential Address',
            'phone_number': 'Phone Number',
            'date_of_birth': 'Date of Birth',
        }


class StudentRegistrationForm(forms.ModelForm):
    """
    Form for registering a new student.
    
    Fields: First/last name, email, address, phone, gender, date of birth, class, and stream enrollment.
    The student must be assigned to a class and stream during registration.
    Admission number is auto-generated during registration.
    """
    class Meta:
        model = Students
        fields = ['fname', 'lname', 'email', 'phone_number', 'date_of_birth', 'gender', 'address', 'class_id', 'stream_id']
        labels = {
            'fname': 'First Name',
            'lname': 'Last Name',
            'email': 'Email Address',
            'phone_number': 'Phone Number',
            'date_of_birth': 'Date of Birth',
            'gender': 'Gender',
            'address': 'Residential Address',
            'class_id': 'Class Enrolled',
            'stream_id': 'Stream Enrolled'
        }
        widgets = {
            'fname': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'}),
            'lname': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email Address'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone Number'}),
            'date_of_birth': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'gender': forms.RadioSelect(attrs={'class': 'form-check-input'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Residential Address'}),
            'class_id': forms.Select(attrs={'class': 'form-control'}),
            'stream_id': forms.Select(attrs={'class': 'form-control'}),
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
        data = args[0] if args else None

        # If no POST data but form has initial (GET) values, use them
        staff_id = None
        stream_id = None

        if data:
            staff_id = data.get('staff')
            stream_id = data.get('stream')
        else:
            # Use initial GET data
            staff_id = self.initial.get('staff')
            stream_id = self.initial.get('stream')

        # Pre-populate staff and stream querysets with ordering
        staff_qs = Staff.objects.all().order_by('fname', 'lname').prefetch_related('subject_specialization')
        self.fields['staff'].queryset = staff_qs

        stream_qs = Streams.objects.select_related('class_id').all().order_by('class_id__class_name', 'stream_name')
        self.fields['stream'].queryset = stream_qs

        # If the form is bound and staff+stream were provided, limit subjects to the intersection
        # between the staff's specializations and the subjects for the selected stream's class.
        try:
            staff_id = int(staff_id) if staff_id else None
        except (ValueError, TypeError):
            staff_id = None

        try:
            stream_id = int(stream_id) if stream_id else None
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


class StaffProfileForm(forms.ModelForm):
    """Simple form for staff to upload or update their profile picture."""
    class Meta:
        model = Staff
        fields = ['profile_pic']
        widgets = {
            'profile_pic': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'profile_pic': 'Profile Picture',
        }


class AcademicYearForm(forms.ModelForm):
    """Form for creating and managing academic years."""
    class Meta:
        model = AcademicYear
        fields = ['year_name', 'start_date', 'end_date', 'is_current']
        widgets = {
            'year_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., 2024/2025'}),
            'start_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'end_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'is_current': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'year_name': 'Academic Year',
            'start_date': 'Start Date',
            'end_date': 'End Date',
            'is_current': 'Mark as Current Academic Year',
        }


class AssignClassTeacherForm(forms.Form):
    """
    Form for assigning a class teacher to a class.
    
    Admin uses this form to:
    1. Select a class
    2. Select a staff member to be the class teacher for that class
    """
    class Meta:
        model = Streams
        fields = ['stream_id', 'staff_id', 'academic_year_id']




# class ClassTeacher(models.Model):
#     id=models.AutoField(primary_key=True)
#     stre_id=models.ForeignKey(Classes, on_delete=models.CASCADE, related_name='class_teachers', null=True, blank=True)
#     stream_id=models.ForeignKey(Streams, on_delete=models.CASCADE, related_name='stream_teachers', null=True, blank=True)
#     staff_id=models.ForeignKey(Staff, on_delete=models.CASCADE, related_name='class_assignments')
#     academic_year=models.ForeignKey(AcademicYear, on_delete=models.CASCADE, related_name='class_teachers', null=True, blank=True)
#     created_at=models.DateTimeField(auto_now_add=True)
#     updated_at=models.DateTimeField(auto_now=True)
#     objects = models.Manager()
    
#     class Meta:
#         unique_together = [['stream_id', 'academic_year']]  # One teacher per stream per academic year
    
#     def __str__(self):
#         if self.stream_id:
#             return f"{self.class_id.class_name} {self.stream_id.stream_name} - {self.staff_id.fname} {self.staff_id.lname}"
#         elif self.class_id:
#             return f"{self.class_id.class_name} - {self.staff_id.fname} {self.staff_id.lname}"
#         return f"{self.staff_id.fname} {self.staff_id.lname}"

