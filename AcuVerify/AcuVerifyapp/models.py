from django.db import models
from django.core.validators import EmailValidator, MinValueValidator, MaxValueValidator

"""
=============================================================================
AcuVerify Models
=============================================================================
This module defines the database models for the AcuVerify school management 
system. Key entities include Staff, Students, Classes, Subjects, Exams, 
Assignments, and Attendance tracking.

Models are organized by domain:
- Administration & Personnel (AdminHOD, Staff, Guardian)
- Academic Structure (EducationLevel, Classes, Streams, Subject)
- Academics (AcademicYear, Term, Exam, Assignment)
- Student Records (Students, StudentGuardian, Attendance, LeaveReport)
- Feedback & Communication (Notifications, Feedback)
=============================================================================
"""


class AdminHOD(models.Model):
    """
    Administrator / Head of Department model.
    Stores admin user credentials for school management.
    
    Fields:
    - fname: First name
    - lname: Last name
    - email: Admin email (used for login)
    - password: Encrypted password (should use Django's User model in production)
    - created_at, updated_at: Audit timestamps
    """
    id=models.AutoField(primary_key=True)
    fname=models.CharField(max_length=255)
    lname=models.CharField(max_length=255)
    email=models.EmailField(max_length=255, validators=[EmailValidator()])
    password=models.CharField(max_length=255)  # Should use hashed passwords in production
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now=True)
    objects = models.Manager()


class Staff(models.Model):
    """
    Teacher/Staff member model.
    Stores information about all school staff members including teachers.
    
    Fields:
    - fname, lname: First and last name
    - email: Staff email (used for login)
    - gender: M (Male) or F (Female)
    - address: Residential address
    - subject_specialization: ManyToMany field linking to subjects the staff specializes in
    - position: Job title (e.g., "Teacher", "Coordinator")
    - department: Department assignment (e.g., "Science", "Languages")
    - phone_number: Contact phone
    
    Related tables:
    - subject_assignments: StaffSubjectStream records (which subjects they teach to which streams)
    - class_assignments: ClassTeacher records (class assignments)
    - feedbacks: FeedbackStaff records
    - exams_created: Exam records created by this staff
    """
    id=models.AutoField(primary_key=True)
    fname=models.CharField(max_length=255)
    lname=models.CharField(max_length=255)
    email=models.EmailField(max_length=255, validators=[EmailValidator()])
    address=models.TextField()
    gender=models.CharField(max_length=10, blank=True, null=True)
    # ManyToMany: allows a staff to specialize in multiple subjects
    subject_specialization=models.ManyToManyField('Subject', blank=True, related_name='specialist_staff')
    position=models.CharField(max_length=255)
    department=models.CharField(max_length=255)
    phone_number=models.CharField(max_length=20, blank=True, null=True)
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now=True)
    objects = models.Manager()
    
    def __str__(self):
        return f"{self.fname} {self.lname}"


class EducationLevel(models.Model):
    """
    Represents education levels in the school system.
    Examples: "Primary", "Junior Secondary", "Senior Secondary"
    
    Fields:
    - level_name: Display name (e.g., "Primary")
    - level_code: Unique code (e.g., "PRIMARY", "JSS", "SSS")
    
    Used by: Classes model to categorize classes by level
    """
    id=models.AutoField(primary_key=True)
    level_name=models.CharField(max_length=100)  # e.g., "Primary", "Junior Secondary", "Senior Secondary"
    level_code=models.CharField(max_length=50, unique=True)  # e.g., "PRIMARY", "JSS", "SSS"
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now=True)
    objects = models.Manager()
    
    def __str__(self):
        return self.level_name
    
    class Meta:
        verbose_name_plural = "Education Levels"


class Classes(models.Model):
    """
    Represents a class/grade level in the school.
    Examples: "Form 1", "Grade 7", "Class 3"
    
    Fields:
    - class_name: Name of the class
    - education_level: ForeignKey to EducationLevel (categorizes the class)
    
    Related tables:
    - streams: Stream records (e.g., Form 1 A, Form 1 B)
    - subjects: Subject records taught in this class
    - students: Student records enrolled in this class
    """
    class_name=models.CharField(max_length=255)  # e.g., "Form 1", "Grade 7", "Class 3"
    education_level=models.ForeignKey(EducationLevel, on_delete=models.CASCADE, null=True, blank=True)
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now=True)
    objects = models.Manager()
    
    def __str__(self):
        return self.class_name

class Streams(models.Model):
    id=models.AutoField(primary_key=True)
    stream_name=models.CharField(max_length=255)  # e.g., "A", "B", "C", "East", "West"
    class_id=models.ForeignKey(Classes, on_delete=models.CASCADE, related_name='streams')
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now=True)
    objects = models.Manager()
    
    def __str__(self):
        return f"{self.class_id.class_name} {self.stream_name}"
    
    class Meta:
        # Prevent duplicate stream names within the same class
        unique_together = [['class_id', 'stream_name']]


class Subject(models.Model):
    id=models.AutoField(primary_key=True)
    subject_name=models.CharField(max_length=255)
    class_id=models.ForeignKey(Classes, on_delete=models.CASCADE, related_name='subjects')
    # Subjects are typically tied to class level, not individual streams
    # All streams in a class usually study the same subjects
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now=True)
    objects=models.Manager()
    
    def __str__(self):
        return self.subject_name


class AcademicYear(models.Model):
    """Academic year e.g., 2024/2025"""
    id=models.AutoField(primary_key=True)
    year_name=models.CharField(max_length=50, unique=True)  # e.g., "2024/2025"
    start_date=models.DateField()
    end_date=models.DateField()
    is_current=models.BooleanField(default=False)  # Mark current academic year
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now=True)
    objects = models.Manager()
    
    def __str__(self):
        return self.year_name
    
    class Meta:
        verbose_name_plural = "Academic Years"


class Term(models.Model):
    """Terms within an academic year: Term 1, Term 2, Term 3"""
    id=models.AutoField(primary_key=True)
    term_name=models.CharField(max_length=50)  # e.g., "Term 1", "Term 2", "Term 3"
    academic_year=models.ForeignKey(AcademicYear, on_delete=models.CASCADE, related_name='terms')
    start_date=models.DateField()
    end_date=models.DateField()
    is_current=models.BooleanField(default=False)  # Mark current term
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now=True)
    objects = models.Manager()
    
    def __str__(self):
        return f"{self.term_name} - {self.academic_year.year_name}"
    
    class Meta:
        unique_together = [['term_name', 'academic_year']]


class StaffSubjectStream(models.Model):
    """
    Links Staff (teachers) to Subjects they teach in specific Streams
    Example: Teacher John teaches Mathematics to Grade 1A, Grade 1B, Grade 1C
    """
    id=models.AutoField(primary_key=True)
    staff_id=models.ForeignKey(Staff, on_delete=models.CASCADE, related_name='subject_assignments')
    subject_id=models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='staff_assignments')
    stream_id=models.ForeignKey(Streams, on_delete=models.CASCADE, related_name='staff_assignments')
    academic_year=models.ForeignKey(AcademicYear, on_delete=models.CASCADE, related_name='staff_subject_streams')
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now=True)
    objects = models.Manager()
    
    class Meta:
        unique_together = [['staff_id', 'subject_id', 'stream_id', 'academic_year']]
        verbose_name_plural = "Staff Subject Stream Assignments"
    
    def __str__(self):
        return f"{self.staff_id.fname} {self.staff_id.lname} - {self.subject_id.subject_name} - {self.stream_id}"


class Guardian(models.Model):
    """
    Guardian/Parent model - can be a standalone parent or linked to Staff
    if the staff member is also a parent in the school
    """
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
    ]
    
    id=models.AutoField(primary_key=True)
    # Optional link to Staff if this guardian is also a staff member
    staff=models.OneToOneField(Staff, on_delete=models.CASCADE, related_name='guardian_profile', null=True, blank=True)
    fname=models.CharField(max_length=255)
    lname=models.CharField(max_length=255)
    email=models.EmailField(max_length=255, validators=[EmailValidator()], blank=True, null=True)
    phone_number=models.CharField(max_length=20)
    gender=models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True, null=True)
    address=models.TextField(blank=True, null=True)
    id_number=models.CharField(max_length=20, blank=True, null=True)  # National ID (important in Kenya)
    occupation=models.CharField(max_length=255, blank=True, null=True)
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now=True)
    objects = models.Manager()
    
    def __str__(self):
        if self.staff:
            return f"{self.fname} {self.lname} (Staff: {self.staff.fname} {self.staff.lname})"
        return f"{self.fname} {self.lname}"
    
    class Meta:
        verbose_name_plural = "Guardians"


class Students(models.Model):
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
    ]
    
    id=models.AutoField(primary_key=True)
    admission_number=models.CharField(max_length=50, unique=True)  # Unique admission number (standard in Kenyan schools)
    fname=models.CharField(max_length=255)
    lname=models.CharField(max_length=255)
    email=models.EmailField(max_length=255, validators=[EmailValidator()], blank=True, null=True)
    phone_number=models.CharField(max_length=20, blank=True, null=True)
    date_of_birth=models.DateField(null=True, blank=True)
    gender=models.CharField(max_length=1, choices=GENDER_CHOICES)
    profile_pic=models.ImageField(upload_to='student_profiles/', blank=True, null=True)  # Use ImageField for file uploads
    password=models.CharField(max_length=255)  # Should use hashed passwords in production
    class_id=models.ForeignKey(Classes, on_delete=models.CASCADE, related_name='students')
    stream_id=models.ForeignKey(Streams, on_delete=models.CASCADE, related_name='students')
    address=models.TextField()
    # Removed parent fields - now using StudentGuardian relationship
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now=True)
    objects = models.Manager()
    
    def __str__(self):
        return f"{self.admission_number} - {self.fname} {self.lname}"
    
    class Meta:
        verbose_name_plural = "Students"


class StudentGuardian(models.Model):
    """
    Junction table linking Students to Guardians with relationship type
    Allows: 
    - One student to have multiple guardians (mum, dad, other)
    - One guardian to have multiple students
    """
    RELATIONSHIP_CHOICES = [
        ('MOTHER', 'Mother'),
        ('FATHER', 'Father'),
        ('GUARDIAN', 'Guardian'),
        ('GRANDMOTHER', 'Grandmother'),
        ('GRANDFATHER', 'Grandfather'),
        ('UNCLE', 'Uncle'),
        ('AUNT', 'Aunt'),
        ('SIBLING', 'Sibling'),
        ('OTHER', 'Other'),
    ]
    
    id=models.AutoField(primary_key=True)
    student_id=models.ForeignKey(Students, on_delete=models.CASCADE, related_name='guardian_relationships')
    guardian_id=models.ForeignKey(Guardian, on_delete=models.CASCADE, related_name='student_relationships')
    relationship_type=models.CharField(max_length=20, choices=RELATIONSHIP_CHOICES)
    is_primary_contact=models.BooleanField(default=False)  # Mark primary contact person
    is_emergency_contact=models.BooleanField(default=False)  # Mark emergency contact
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now=True)
    objects = models.Manager()
    
    class Meta:
        unique_together = [['student_id', 'guardian_id']]  # One relationship record per student-guardian pair
        verbose_name_plural = "Student Guardian Relationships"
    
    def __str__(self):
        return f"{self.student_id.fname} {self.student_id.lname} - {self.get_relationship_type_display()} ({self.guardian_id.fname} {self.guardian_id.lname})"





class Attendance(models.Model):
    id=models.AutoField(primary_key=True)
    subject_id=models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='attendances')
    attendance_date=models.DateField()  # Changed from DateTimeField to DateField for attendance
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now=True)
    objects = models.Manager()
    
    class Meta:
        unique_together = [['subject_id', 'attendance_date']]  # One attendance record per subject per day

class AttendanceReport(models.Model):
    id=models.AutoField(primary_key=True)
    student_id=models.ForeignKey(Students, on_delete=models.CASCADE, related_name='attendance_reports')
    attendance_id=models.ForeignKey(Attendance, on_delete=models.CASCADE, related_name='reports')
    status=models.BooleanField(default=False)  # True = Present, False = Absent
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now=True)
    objects = models.Manager()
    
    class Meta:
        unique_together = [['student_id', 'attendance_id']]  # One record per student per attendance


class LeaveReport(models.Model):
    LEAVE_STATUS_CHOICES = [
        (0, 'Pending'),
        (1, 'Approved'),
        (2, 'Rejected'),
    ]
    
    id=models.AutoField(primary_key=True)
    student_id=models.ForeignKey(Students, on_delete=models.CASCADE, related_name='leave_reports')
    leave_date=models.DateField()  # Changed from CharField to DateField
    leave_message=models.TextField()
    leave_status=models.IntegerField(choices=LEAVE_STATUS_CHOICES, default=0)  # Changed to IntegerField for better status tracking
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now=True)
    objects = models.Manager()



class FeedbackStudent(models.Model):
    id=models.AutoField(primary_key=True)
    student_id=models.ForeignKey(Students, on_delete=models.CASCADE, related_name='feedbacks')
    feedback_message=models.TextField()
    feedback_reply=models.TextField(blank=True, null=True)
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now=True)
    objects = models.Manager()


class FeedbackStaff(models.Model):
    id=models.AutoField(primary_key=True)
    staff_id=models.ForeignKey(Staff, on_delete=models.CASCADE, related_name='feedbacks')
    feedback_message=models.TextField()
    feedback_reply=models.TextField(blank=True, null=True)
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now=True)
    objects = models.Manager()



class NotificationStudent(models.Model):
    id=models.AutoField(primary_key=True)
    student_id=models.ForeignKey(Students, on_delete=models.CASCADE, related_name='notifications')
    message=models.TextField()
    is_read=models.BooleanField(default=False)
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now=True)
    objects = models.Manager()


class NotificationStaff(models.Model):
    id=models.AutoField(primary_key=True)
    staff_id=models.ForeignKey(Staff, on_delete=models.CASCADE, related_name='notifications')
    message=models.TextField()
    is_read=models.BooleanField(default=False)
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now=True)
    objects = models.Manager()


class NotificationGuardian(models.Model):
    """Notifications for guardians about their children"""
    id=models.AutoField(primary_key=True)
    guardian_id=models.ForeignKey(Guardian, on_delete=models.CASCADE, related_name='notifications')
    student_id=models.ForeignKey(Students, on_delete=models.CASCADE, related_name='guardian_notifications', null=True, blank=True)
    # If student_id is null, it's a general notification to all their children
    message=models.TextField()
    is_read=models.BooleanField(default=False)
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now=True)
    objects = models.Manager()
    
    def __str__(self):
        if self.student_id:
            return f"{self.guardian_id.fname} {self.guardian_id.lname} - {self.student_id.fname} {self.student_id.lname}"
        return f"{self.guardian_id.fname} {self.guardian_id.lname} - General"

# Additional model for class teacher assignment (important in Kenyan schools)
class ClassTeacher(models.Model):
    id=models.AutoField(primary_key=True)
    class_id=models.ForeignKey(Classes, on_delete=models.CASCADE, related_name='class_teachers', null=True, blank=True)
    stream_id=models.ForeignKey(Streams, on_delete=models.CASCADE, related_name='stream_teachers', null=True, blank=True)
    staff_id=models.ForeignKey(Staff, on_delete=models.CASCADE, related_name='class_assignments')
    academic_year=models.ForeignKey(AcademicYear, on_delete=models.CASCADE, related_name='class_teachers', null=True, blank=True)
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now=True)
    objects = models.Manager()
    
    class Meta:
        unique_together = [['stream_id', 'academic_year']]  # One teacher per stream per academic year
    
    def __str__(self):
        if self.stream_id:
            return f"{self.class_id.class_name} {self.stream_id.stream_name} - {self.staff_id.fname} {self.staff_id.lname}"
        elif self.class_id:
            return f"{self.class_id.class_name} - {self.staff_id.fname} {self.staff_id.lname}"
        return f"{self.staff_id.fname} {self.staff_id.lname}"


class Exam(models.Model):
    """
    Exam definition - defines an exam that will have marks recorded
    Examples: Mid-term Exam, End of Term Exam, CAT, Assignment, etc.
    """
    EXAM_TYPE_CHOICES = [
        ('CAT', 'Continuous Assessment Test (CAT)'),
        ('MID_TERM', 'Mid-Term Exam'),
        ('END_TERM', 'End of Term Exam'),
        ('ASSIGNMENT', 'Assignment'),
        ('PROJECT', 'Project'),
        ('PRACTICAL', 'Practical'),
        ('QUIZ', 'Quiz'),
        ('OTHER', 'Other'),
    ]
    
    id=models.AutoField(primary_key=True)
    exam_name=models.CharField(max_length=255)  # e.g., "Mid-Term Exam", "CAT 1", "End of Term"
    exam_type=models.CharField(max_length=20, choices=EXAM_TYPE_CHOICES)
    subject_id=models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='exams')
    stream_id=models.ForeignKey(Streams, on_delete=models.CASCADE, related_name='exams')
    term=models.ForeignKey(Term, on_delete=models.CASCADE, related_name='exams')
    total_marks=models.DecimalField(max_digits=5, decimal_places=2)  # e.g., 100.00
    exam_date=models.DateField(null=True, blank=True)  # Date exam was/will be conducted
    created_by=models.ForeignKey(Staff, on_delete=models.SET_NULL, null=True, related_name='exams_created')
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now=True)
    objects = models.Manager()
    
    class Meta:
        verbose_name_plural = "Exams"
    
    def __str__(self):
        return f"{self.exam_name} - {self.subject_id.subject_name} - {self.stream_id} - {self.term}"


class StudentExamMark(models.Model):
    """
    Stores individual student marks for exams
    Uploaded/recorded by the teacher who teaches the subject to that stream
    """
    id=models.AutoField(primary_key=True)
    student_id=models.ForeignKey(Students, on_delete=models.CASCADE, related_name='exam_marks')
    exam_id=models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='student_marks')
    marks_obtained=models.DecimalField(max_digits=5, decimal_places=2)  # Marks the student got
    # calculated_percentage can be computed from (marks_obtained / exam.total_marks) * 100
    remarks=models.TextField(blank=True, null=True)  # Teacher's remarks about the student's performance
    uploaded_by=models.ForeignKey(Staff, on_delete=models.SET_NULL, null=True, related_name='marks_uploaded')
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now=True)
    objects = models.Manager()
    
    class Meta:
        unique_together = [['student_id', 'exam_id']]  # One mark record per student per exam
        verbose_name_plural = "Student Exam Marks"
    
    def __str__(self):
        return f"{self.student_id.fname} {self.student_id.lname} - {self.exam_id.exam_name} - {self.marks_obtained}/{self.exam_id.total_marks}"
    
    @property
    def percentage(self):
        """Calculate percentage score"""
        if self.exam_id.total_marks > 0:
            return (self.marks_obtained / self.exam_id.total_marks) * 100
        return 0
    
    @property
    def grade(self):
        """Calculate grade based on percentage (Kenyan grading system)"""
        percentage = self.percentage
        if percentage >= 80:
            return 'A'
        elif percentage >= 75:
            return 'A-'
        elif percentage >= 70:
            return 'B+'
        elif percentage >= 65:
            return 'B'
        elif percentage >= 60:
            return 'B-'
        elif percentage >= 55:
            return 'C+'
        elif percentage >= 50:
            return 'C'
        elif percentage >= 45:
            return 'C-'
        elif percentage >= 40:
            return 'D+'
        elif percentage >= 35:
            return 'D'
        else:
            return 'E'


class Assignment(models.Model):
    """
    Assignment/Homework uploaded by teachers for students
    Can be assigned during holidays or regular school periods
    Parents can view assignments to ensure students complete them on time
    """
    ASSIGNMENT_TYPE_CHOICES = [
        ('HOMEWORK', 'Homework'),
        ('HOLIDAY_ASSIGNMENT', 'Holiday Assignment'),
        ('PROJECT', 'Project'),
        ('REVISION', 'Revision Work'),
        ('OTHER', 'Other'),
    ]
    
    id=models.AutoField(primary_key=True)
    title=models.CharField(max_length=255)
    description=models.TextField()  # Detailed instructions for the assignment
    assignment_type=models.CharField(max_length=20, choices=ASSIGNMENT_TYPE_CHOICES, default='HOMEWORK')
    subject_id=models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='assignments')
    stream_id=models.ForeignKey(Streams, on_delete=models.CASCADE, related_name='assignments')
    term=models.ForeignKey(Term, on_delete=models.CASCADE, related_name='assignments', null=True, blank=True)
    created_by=models.ForeignKey(Staff, on_delete=models.CASCADE, related_name='assignments_created')
    assignment_file=models.FileField(upload_to='assignments/', blank=True, null=True)  # Optional file attachment
    total_marks=models.DecimalField(max_digits=5, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    due_date=models.DateTimeField()  # Deadline for submission
    is_active=models.BooleanField(default=True)  # Can be deactivated if needed
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now=True)
    objects = models.Manager()
    
    class Meta:
        verbose_name_plural = "Assignments"
        ordering = ['-due_date', '-created_at']  # Show latest/future assignments first
    
    def __str__(self):
        return f"{self.title} - {self.subject_id.subject_name} - {self.stream_id}"
    
    @property
    def is_overdue(self):
        """Check if assignment due date has passed"""
        from django.utils import timezone
        return timezone.now() > self.due_date
    
    @property
    def days_remaining(self):
        """Calculate days remaining until due date"""
        from django.utils import timezone
        if timezone.now() < self.due_date:
            delta = self.due_date - timezone.now()
            return delta.days
        return 0


class StudentAssignmentSubmission(models.Model):
    """
    Tracks student submissions for assignments
    Parents can view this to check if their child has completed assignments
    """
    SUBMISSION_STATUS_CHOICES = [
        ('NOT_STARTED', 'Not Started'),
        ('IN_PROGRESS', 'In Progress'),
        ('SUBMITTED', 'Submitted'),
        ('LATE', 'Submitted Late'),
        ('GRADED', 'Graded'),
    ]
    
    id=models.AutoField(primary_key=True)
    assignment_id=models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name='submissions')
    student_id=models.ForeignKey(Students, on_delete=models.CASCADE, related_name='assignment_submissions')
    status=models.CharField(max_length=20, choices=SUBMISSION_STATUS_CHOICES, default='NOT_STARTED')
    submission_file=models.FileField(upload_to='assignment_submissions/', blank=True, null=True)  # Student's submitted work
    submission_text=models.TextField(blank=True, null=True)  # Text-based submission (for online assignments)
    submission_date=models.DateTimeField(null=True, blank=True)  # When student submitted
    marks_obtained=models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(0)])
    remarks=models.TextField(blank=True, null=True)  # Teacher's feedback/remarks
    graded_by=models.ForeignKey(Staff, on_delete=models.SET_NULL, null=True, blank=True, related_name='graded_assignments')
    graded_at=models.DateTimeField(null=True, blank=True)  # When teacher graded the assignment
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now=True)
    objects = models.Manager()
    
    class Meta:
        unique_together = [['assignment_id', 'student_id']]  # One submission per student per assignment
        verbose_name_plural = "Student Assignment Submissions"
        ordering = ['-submission_date', '-created_at']
    
    def __str__(self):
        return f"{self.student_id.fname} {self.student_id.lname} - {self.assignment_id.title} - {self.get_status_display()}"
    
    @property
    def is_submitted(self):
        """Check if assignment has been submitted"""
        return self.status in ['SUBMITTED', 'LATE', 'GRADED']
    
    @property
    def is_late(self):
        """Check if submission was late"""
        if self.submission_date and self.assignment_id.due_date:
            return self.submission_date > self.assignment_id.due_date
        return False
    
    @property
    def percentage_score(self):
        """Calculate percentage score if graded"""
        if self.marks_obtained and self.assignment_id.total_marks > 0:
            return (self.marks_obtained / self.assignment_id.total_marks) * 100
        return None
    
    def save(self, *args, **kwargs):
        """Override save to automatically update status and check if late"""
        if self.submission_date and not self.status == 'GRADED':
            if self.is_late:
                self.status = 'LATE'
            else:
                self.status = 'SUBMITTED'
        super().save(*args, **kwargs)
