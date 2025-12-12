"""
=============================================================================
AcuVerify Views
=============================================================================
This module contains all view functions for the AcuVerify school management
system. Views handle:

1. Authentication (multi-step login, password creation)
2. Staff registration and management
3. Student registration
4. Stream assignment (admin only)
5. Academic administration

Authentication uses a custom multi-step process:
- Step 1: User enters email to check existence
- Step 2a: Existing users enter password
- Step 2b: New staff/students create a password and auto-create Django User
=============================================================================
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login as auth_login, logout as auth_logout, authenticate
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from .models import Staff, Students
from .forms import StaffRegistrationForm, StudentRegistrationForm, EmailForm, PasswordForm, CreatePasswordForm, AssignStreamForm
from .models import StaffSubjectStream, Subject, Streams, AcademicYear, Assignment, StudentAssignmentSubmission
from .forms import StaffProfileForm, AssignmentForm, StudentAssignmentSubmissionForm, AssignmentGradingForm


# ============================================================================
# PERMISSION CHECKING HELPERS
# ============================================================================

def get_staff_or_none(user):
    """Get Staff object for logged-in user or return None"""
    try:
        return Staff.objects.get(email=user.email)
    except Staff.DoesNotExist:
        return None


def get_student_or_none(user):
    """Get Students object for logged-in user or return None"""
    try:
        return Students.objects.get(email=user.email)
    except Students.DoesNotExist:
        return None


def is_teacher(user):
    """Check if user is a staff/teacher"""
    return get_staff_or_none(user) is not None


def is_student(user):
    """Check if user is a student"""
    return get_student_or_none(user) is not None


def teacher_can_teach(staff, subject_id, stream_id):
    """Check if a teacher teaches the given subject in the given stream"""
    return StaffSubjectStream.objects.filter(
        staff_id=staff,
        subject_id=subject_id,
        stream_id=stream_id
    ).exists()


def home(request):
    """
    Home page view. Displays dashboard/landing page.
    """
    return render(request, 'home.html')


def login_user(request):
    """
    Multi-step authentication view.
    
    Process:
    1. Email submission: check if user exists in User, Staff, or Students table
    2. Existing users: enter password for Django User authentication
    3. New users (Staff/Students): create new password and auto-generate Django User
    
    Session variables track progress: 'step', 'login_email', 'user_type', 'staff_id', 'student_id'
    
    URL param: ?reset=true clears session to start over
    """
    # Reset session if requested
    if request.GET.get('reset') == 'true':
        request.session.pop('login_email', None)
        request.session.pop('step', None)
        request.session.pop('user_type', None)
        request.session.pop('staff_id', None)
        request.session.pop('student_id', None)
        return redirect('login')
    
    # Step 1: Email entry and validation
    if 'step' not in request.session or request.session.get('step') == 'email':
        if request.method == 'POST':
            email_form = EmailForm(request.POST)
            if email_form.is_valid():
                email = email_form.cleaned_data['email'].lower()
                
                # Check if email exists in Django User table (existing users)
                try:
                    user = User.objects.get(email=email)
                    # User exists, go to password step
                    request.session['login_email'] = email
                    request.session['step'] = 'password'
                    request.session['user_type'] = 'existing_user'
                    return redirect('login')
                except User.DoesNotExist:
                    # Check Staff table (registered staff without password yet)
                    try:
                        staff = Staff.objects.get(email__iexact=email)
                        request.session['login_email'] = email
                        request.session['step'] = 'create_password'
                        request.session['user_type'] = 'staff'
                        request.session['staff_id'] = staff.id
                        return redirect('login')
                    except Staff.DoesNotExist:
                        # Check Students table (registered students without password yet)
                        try:
                            student = Students.objects.get(email__iexact=email)
                            request.session['login_email'] = email
                            request.session['step'] = 'create_password'
                            request.session['user_type'] = 'student'
                            request.session['student_id'] = student.id
                            return redirect('login')
                        except Students.DoesNotExist:
                            messages.error(request, 'A user with this email does not exist.')
                            email_form = EmailForm()
        else:
            email_form = EmailForm()
        
        return render(request, 'login.html', {'form': email_form, 'step': 'email'})
    
    # Step 2a: Existing user - enter password and authenticate
    elif request.session.get('step') == 'password':
        if request.method == 'POST':
            password_form = PasswordForm(request.POST)
            if password_form.is_valid():
                email = request.session.get('login_email')
                password = password_form.cleaned_data['password']
                
                # Authenticate against Django User model
                try:
                    user = User.objects.get(email=email)
                    user = authenticate(request, username=user.username, password=password)
                    if user is not None:
                        auth_login(request, user)
                        # Clear session
                        request.session.pop('login_email', None)
                        request.session.pop('step', None)
                        request.session.pop('user_type', None)
                        messages.success(request, 'Login successful!')
                        return redirect('home')
                    else:
                        messages.error(request, 'Invalid password.')
                except User.DoesNotExist:
                    messages.error(request, 'User not found.')
                    request.session.pop('login_email', None)
                    request.session.pop('step', None)
                    request.session.pop('user_type', None)
                    return redirect('login')
        else:
            password_form = PasswordForm()
        
        return render(request, 'login.html', {
            'form': password_form, 
            'step': 'password',
            'email': request.session.get('login_email')
        })
    
    # Step 2b: New user (Staff/Student) - create password
    elif request.session.get('step') == 'create_password':
        if request.method == 'POST':
            create_password_form = CreatePasswordForm(request.POST)
            if create_password_form.is_valid():
                email = request.session.get('login_email')
                password = create_password_form.cleaned_data['password']
                user_type = request.session.get('user_type')
                
                # Create User account
                try:
                    # Use email as username (or generate unique username if email already taken as username)
                    username = email.split('@')[0]
                    counter = 1
                    while User.objects.filter(username=username).exists():
                        username = f"{email.split('@')[0]}{counter}"
                        counter += 1
                    
                    user = User.objects.create_user(
                        username=username,
                        email=email,
                        password=password
                    )
                    
                    # Log in the user
                    auth_login(request, user)
                    
                    # Clear session
                    request.session.pop('login_email', None)
                    request.session.pop('step', None)
                    request.session.pop('user_type', None)
                    request.session.pop('staff_id', None)
                    request.session.pop('student_id', None)
                    
                    messages.success(request, f'Password created successfully! Welcome, {user_type.title()}!')
                    return redirect('home')
                except Exception as e:
                    messages.error(request, f'Error creating account: {str(e)}')
        else:
            create_password_form = CreatePasswordForm()
        
        user_type = request.session.get('user_type', 'user')
        return render(request, 'login.html', {
            'form': create_password_form,
            'step': 'create_password',
            'email': request.session.get('login_email'),
            'user_type': user_type
        })
    
    # Default: reset to email step
    else:
        request.session.pop('login_email', None)
        request.session.pop('step', None)
        request.session.pop('user_type', None)
        return redirect('login')

def register_staff(request):
    """
    Staff registration view.
    
    GET: Shows staff registration form
    POST: Saves new staff member with their specializations
    
    The form auto-creates standard Kenyan subjects if they don't exist,
    and allows the registrant to select multiple subject specializations.
    
    After successful registration, admin must explicitly assign the staff to
    streams/classes using the assign_stream view.
    """
    if request.method == 'POST':
        form = StaffRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Staff member registered successfully!')
            return redirect('staff_list')
    else:
        form = StaffRegistrationForm()
    return render(request, 'staffregistrationform.html', {'form': form})

        
def register_student(request):
    """
    Student registration view.
    
    GET: Shows student registration form
    POST: Saves new student with class and stream assignment
    
    Students must be assigned to a specific class and stream during registration.
    Admission number is auto-generated in sequence: std1, std2, std3, etc.
    """
    if request.method == 'POST':
        form = StudentRegistrationForm(request.POST)
        if form.is_valid():
            student = form.save(commit=False)
            # Auto-generate admission number
            student.admission_number = Students.generate_admission_number()
            student.save()
            messages.success(request, f'Student registered successfully! Admission Number: {student.admission_number}')
            return redirect('student_list')
    else:
        form = StudentRegistrationForm()
    return render(request, 'studentregistration.html', {'form': form})


def logout_user(request):
    """
    Logs out the current user and clears session.
    Redirects to login page.
    """
    auth_logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('login')


def accademic_view(request):
    """
    Academic administration page.
    Placeholder for academic management features (exams, assignments, etc.).
    """
    return render(request, 'accademic.html')


@login_required
def staff_list(request):
    """
    List all staff members.
    Requires authentication.
    """
    staff_members = Staff.objects.all().order_by('fname', 'lname')
    return render(request, 'staff_list.html', {'staff_members': staff_members})


@login_required
def edit_staff(request, pk):
    """
    Edit an existing staff member's information.
    
    Args:
        pk: Primary key of the staff member to edit
    
    GET: Shows the form pre-filled with current data
    POST: Updates staff information and redirects to staff list
    """
    staff = get_object_or_404(Staff, pk=pk)
    if request.method == 'POST':
        form = StaffRegistrationForm(request.POST, instance=staff)
        if form.is_valid():
            form.save()
            messages.success(request, 'Staff updated successfully.')
            return redirect('staff_list')
    else:
        form = StaffRegistrationForm(instance=staff)
    return render(request, 'staffregistrationform.html', {'form': form, 'editing': True, 'staff_obj': staff})


@login_required
def edit_profile(request):
    """Allow authenticated staff to upload or update their profile picture.

    The staff instance is resolved by matching the logged-in user's email
    to the Staff.email field. If no Staff record exists for the user the
    view will show a message and redirect.
    """
    user = request.user
    # Attempt to find a Staff record with matching email
    try:
        staff = Staff.objects.get(email__iexact=user.email)
    except Staff.DoesNotExist:
        messages.error(request, 'No staff profile found for your account.')
        return redirect('home')

    if request.method == 'POST':
        form = StaffProfileForm(request.POST, request.FILES, instance=staff)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully.')
            return redirect('edit_profile')
    else:
        form = StaffProfileForm(instance=staff)

    return render(request, 'edit_profile.html', {'form': form, 'staff_obj': staff})


@login_required
def delete_staff(request, pk):
    """
    Delete a staff member (with confirmation).
    
    Args:
        pk: Primary key of the staff member to delete
    
    GET: Shows confirmation page
    POST: Deletes the staff member and redirects to staff list
    """
    staff = get_object_or_404(Staff, pk=pk)
    if request.method == 'POST':
        staff.delete()
        messages.success(request, 'Staff deleted successfully.')
        return redirect('staff_list')
    return render(request, 'staff_delete_confirm.html', {'staff_obj': staff})


@login_required
def assign_stream(request):
    """
    Admin view to assign streams/classes and subjects to a teacher.
    
    This is a core feature that links Staff to their teaching assignments:
    - Staff member
    - Specific stream/class they'll teach
    - Specific subjects for that stream (filtered to their specializations)
    
    Process:
    1. Admin selects a staff member
    2. Admin selects a stream/class
    3. Form dynamically filters subjects to show only:
       - Subjects for that stream's class
       - Subjects matching the teacher's specialization
    4. Admin selects which subjects to assign
    5. System creates StaffSubjectStream entries (one per subject) for the current academic year
    
    Uses get_or_create to prevent duplicate assignments.
    
    Requires authentication (login_required decorator).
    """
    currently_assigned_subjects = []
    
    # Check if any academic year exists
    has_academic_year = AcademicYear.objects.exists()
    if not has_academic_year:
        messages.warning(request, 'No academic years found. Please create an academic year first before assigning teachers to streams.')
    
    if request.method == 'POST':
        # Prevent assignment if no academic year exists
        if not has_academic_year:
            messages.error(request, 'Cannot assign streams without an academic year. Please create one in Manage Academic Years.')
            return redirect('manage_academic_year')
        
        form = AssignStreamForm(request.POST)
        if form.is_valid():
            staff = form.cleaned_data['staff']
            stream = form.cleaned_data['stream']
            subjects = form.cleaned_data['subjects']

            # Determine current academic year (or fall back to latest year)
            year = AcademicYear.objects.filter(is_current=True).first()
            if not year:
                year = AcademicYear.objects.order_by('-start_date').first()

            # Create StaffSubjectStream record for each selected subject
            created = 0
            for subj in subjects:
                obj, created_flag = StaffSubjectStream.objects.get_or_create(
                    staff_id=staff,
                    subject_id=subj,
                    stream_id=stream,
                    academic_year=year
                )
                if created_flag:
                    created += 1

            messages.success(request, f'Assigned {created} subject(s) to {staff.fname} {staff.lname} for {stream}.')
            return redirect('assign_stream')
    else:
        form = AssignStreamForm()
    
    # If a staff and stream are selected (GET with params or after form submission attempt),
    # fetch the subjects already assigned to that teacher for that stream
    staff_id = request.GET.get('staff') or request.POST.get('staff')
    stream_id = request.GET.get('stream') or request.POST.get('stream')
    
    if staff_id and stream_id and has_academic_year:
        try:
            year = AcademicYear.objects.filter(is_current=True).first()
            if not year:
                year = AcademicYear.objects.order_by('-start_date').first()
            
            # Get subjects already assigned to this teacher for this stream in the current year
            currently_assigned_subjects = StaffSubjectStream.objects.filter(
                staff_id=staff_id,
                stream_id=stream_id,
                academic_year=year
            ).values_list('subject_id', flat=True)
        except (ValueError, TypeError):
            currently_assigned_subjects = []

    return render(request, 'assign_stream.html', {
        'form': form,
        'currently_assigned_subjects': list(currently_assigned_subjects),
        'has_academic_year': has_academic_year
    })

@login_required
def student_list(request):
        """
        List all registered students.
        Requires authentication.
        """
        students = Students.objects.all().order_by('fname', 'lname')
        return render(request, 'student_list.html', {'students': students})


def edit_student(request, pk):
    """
    Edit an existing student's information.
    
    Args:
        pk: Primary key of the student to edit
    
    GET: Shows the form pre-filled with current data
    POST: Updates student information and redirects to student list
    """
    student = get_object_or_404(Students, pk=pk)
    if request.method == 'POST':
        form = StudentRegistrationForm(request.POST, instance=student)
        if form.is_valid():
            form.save()
            messages.success(request, 'Student updated successfully.')
            return redirect('student_list')
    else:
        form = StudentRegistrationForm(instance=student)
    return render(request, 'studentregistration.html', {'form': form, 'editing': True, 'student_obj': student})



def delete_student(request, pk):
    """
    Delete a student (with confirmation).
    
    Args:
        pk: Primary key of the student to delete
    
    GET: Shows confirmation page
    POST: Deletes the student and redirects to student list
    """
    student = get_object_or_404(Students, pk=pk)
    if request.method == 'POST':
        student.delete()
        messages.success(request, 'Student deleted successfully.')
        return redirect('student_list')
    return render(request, 'student_delete_confirm.html', {'student_obj': student})            

from django.http import JsonResponse

@login_required
@login_required
def get_teacher_subjects(request):
    """
    AJAX endpoint to fetch subjects for a teacher in a specific stream.
    
    Returns subjects that:
    1. Belong to the selected stream's class
    2. Match the teacher's specializations (by subject name)
    
    This allows teachers to teach the same subjects across different classes.
    """
    staff_id = request.GET.get('staff_id')
    stream_id = request.GET.get('stream_id')
    subjects = []

    if staff_id and stream_id:
        try:
            staff = Staff.objects.get(id=staff_id)
            stream = Streams.objects.select_related('class_id').get(id=stream_id)
            
            # Get the teacher's specialization subject names
            teacher_subjects = staff.subject_specialization.values_list('subject_name', flat=True)
            
            # Get subjects for this stream's class that match teacher's specializations
            qs = Subject.objects.filter(
                classes=stream.class_id,
                subject_name__in=teacher_subjects
            ).order_by('subject_name')
            
            subjects = [{'id': s.id, 'name': s.subject_name} for s in qs]
        except (Staff.DoesNotExist, Streams.DoesNotExist):
            pass

    return JsonResponse({'subjects': subjects})


@login_required
def manage_academic_year(request):
    """
    Manage academic years: create new years and view existing ones.
    Only allows users to add academic years, not delete them (for data integrity).
    """
    from .forms import AcademicYearForm
    
    if request.method == 'POST':
        form = AcademicYearForm(request.POST)
        if form.is_valid():
            academic_year = form.save()
            messages.success(request, f"Academic year '{academic_year.year_name}' created successfully!")
            return redirect('manage_academic_year')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = AcademicYearForm()
    
    # Get all academic years, ordered by start_date descending (newest first)
    academic_years = AcademicYear.objects.all().order_by('-start_date')
    current_year = AcademicYear.objects.filter(is_current=True).first()
    
    context = {
        'form': form,
        'academic_years': academic_years,
        'current_year': current_year,
    }
    
    return render(request, 'academic_year.html', context)


# ============================================================================
# ASSIGNMENT MANAGEMENT VIEWS
# ============================================================================

@login_required
def teacher_assignments(request):
    """
    Teacher view to see assignments they have posted.
    Only shows assignments created by the logged-in teacher.
    """
    try:
        staff = Staff.objects.get(email=request.user.email)
    except Staff.DoesNotExist:
        messages.error(request, 'You are not registered as a staff member.')
        return redirect('home')
    
    # Get all assignments created by this teacher, ordered by due_date
    assignments = Assignment.objects.filter(created_by=staff).order_by('-due_date', '-created_at')
    
    context = {
        'assignments': assignments,
        'is_teacher': True,
    }
    return render(request, 'assignments/teacher_list.html', context)


@login_required
def create_assignment(request):
    """
    Teacher view to create and post a new assignment.
    
    GET: Show assignment form
    POST: Save assignment (teacher can only assign to streams/subjects they teach)
    """
    try:
        staff = Staff.objects.get(email=request.user.email)
    except Staff.DoesNotExist:
        messages.error(request, 'You are not registered as a staff member.')
        return redirect('home')
    
    if request.method == 'POST':
        form = AssignmentForm(request.POST, request.FILES)
        if form.is_valid():
            assignment = form.save(commit=False)
            # Verify teacher teaches this subject/stream combination
            if not teacher_can_teach(staff, assignment.subject_id.id, assignment.stream_id.id):
                messages.error(request, 'You do not have permission to create assignments for this subject/stream combination.')
                return redirect('teacher_assignments')
            assignment.created_by = staff
            assignment.save()
            messages.success(request, f'Assignment "{assignment.title}" posted successfully!')
            return redirect('teacher_assignments')
    else:
        form = AssignmentForm()
        # Filter to only streams the teacher teaches
        teacher_streams = StaffSubjectStream.objects.filter(staff_id=staff).values_list('stream_id', flat=True).distinct()
        form.fields['stream_id'].queryset = Streams.objects.filter(id__in=teacher_streams)
        
        # Filter to only subjects the teacher teaches
        teacher_subjects = StaffSubjectStream.objects.filter(staff_id=staff).values_list('subject_id', flat=True).distinct()
        form.fields['subject_id'].queryset = Subject.objects.filter(id__in=teacher_subjects)
    
    context = {
        'form': form,
        'title': 'Create Assignment',
    }
    return render(request, 'assignments/assignment_form.html', context)


@login_required
def teacher_assignment_detail(request, pk):
    """
    Teacher view to see assignment details, submissions, and grade students.
    """
    assignment = get_object_or_404(Assignment, pk=pk)
    
    try:
        staff = Staff.objects.get(email=request.user.email)
    except Staff.DoesNotExist:
        messages.error(request, 'You are not registered as a staff member.')
        return redirect('home')
    
    # Only the teacher who created the assignment can view this
    if assignment.created_by != staff:
        messages.error(request, 'You do not have permission to view this assignment.')
        return redirect('teacher_assignments')
    
    # Get all submissions for this assignment
    submissions = StudentAssignmentSubmission.objects.filter(assignment_id=assignment.id).select_related('student_id')
    
    context = {
        'assignment': assignment,
        'submissions': submissions,
        'is_teacher': True,
    }
    return render(request, 'assignments/teacher_assignment_detail.html', context)


@login_required
def grade_submission(request, submission_pk):
    """
    Teacher view to grade a student submission.
    """
    submission = get_object_or_404(StudentAssignmentSubmission.objects.select_related('assignment_id', 'student_id'), pk=submission_pk)
    
    try:
        staff = Staff.objects.get(email=request.user.email)
    except Staff.DoesNotExist:
        messages.error(request, 'You are not registered as a staff member.')
        return redirect('home')
    
    # Only the teacher who created the assignment can grade
    if submission.assignment_id.created_by != staff:
        messages.error(request, 'You do not have permission to grade this submission.')
        return redirect('teacher_assignments')
    
    if request.method == 'POST':
        form = AssignmentGradingForm(request.POST, instance=submission)
        if form.is_valid():
            submission = form.save(commit=False)
            submission.status = 'GRADED'
            submission.graded_by = staff
            submission.graded_at = timezone.now()
            submission.save()
            messages.success(request, f'Submission graded for {submission.student_id.fname} {submission.student_id.lname}.')
            return redirect('teacher_assignment_detail', pk=submission.assignment_id.id)
    else:
        form = AssignmentGradingForm(instance=submission)
    
    context = {
        'form': form,
        'submission': submission,
        'assignment': submission.assignment_id,
        'is_teacher': True,
    }
    return render(request, 'assignments/grade_submission.html', context)


@login_required
def student_assignments(request):
    """
    Student view to see assignments for their stream/class.
    """
    try:
        student = Students.objects.get(email=request.user.email)
    except Students.DoesNotExist:
        messages.error(request, 'You are not registered as a student.')
        return redirect('home')
    
    # Get assignments for the student's stream
    assignments = Assignment.objects.filter(stream_id=student.stream_id).order_by('-due_date', '-created_at')
    
    # Get submissions for this student
    submissions = StudentAssignmentSubmission.objects.filter(student_id=student).values_list('assignment_id', flat=True)
    
    context = {
        'assignments': assignments,
        'submissions': list(submissions),
        'is_student': True,
    }
    return render(request, 'assignments/student_list.html', context)


@login_required
def student_assignment_detail(request, pk):
    """
    Student view to see assignment details and submit work.
    """
    assignment = get_object_or_404(Assignment, pk=pk)
    
    try:
        student = Students.objects.get(email=request.user.email)
    except Students.DoesNotExist:
        messages.error(request, 'You are not registered as a student.')
        return redirect('home')
    
    # Verify student is in the correct stream
    if assignment.stream_id != student.stream_id:
        messages.error(request, 'You do not have access to this assignment.')
        return redirect('student_assignments')
    
    # Get or create submission record
    submission, created = StudentAssignmentSubmission.objects.get_or_create(
        assignment_id=assignment.id,
        student_id=student.id
    )
    
    if request.method == 'POST':
        form = StudentAssignmentSubmissionForm(request.POST, request.FILES, instance=submission)
        if form.is_valid():
            submission = form.save(commit=False)
            submission.submission_date = timezone.now()
            submission.status = 'SUBMITTED'
            submission.save()
            messages.success(request, 'Assignment submitted successfully!')
            return redirect('student_assignment_detail', pk=pk)
    else:
        form = StudentAssignmentSubmissionForm(instance=submission)
    
    context = {
        'assignment': assignment,
        'submission': submission,
        'form': form,
        'is_student': True,
    }
    return render(request, 'assignments/student_assignment_detail.html', context)


@login_required
def parent_assignments(request):
    """
    Parent view to see assignments for their child(ren).
    Parents can view and comment but cannot grade or submit.
    """
    try:
        # Find the student linked to this user (via email)
        student = Students.objects.get(email=request.user.email)
    except Students.DoesNotExist:
        messages.error(request, 'You do not have a student profile.')
        return redirect('home')
    
    # Get assignments for the student's stream
    assignments = Assignment.objects.filter(stream_id=student.stream_id).order_by('-due_date', '-created_at')
    
    # Get submissions for the student
    submissions = StudentAssignmentSubmission.objects.filter(student_id=student).select_related('assignment_id')
    
    context = {
        'assignments': assignments,
        'submissions': submissions,
        'student': student,
        'is_parent': True,
    }
    return render(request, 'assignments/parent_list.html', context)
