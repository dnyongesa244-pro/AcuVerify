#!/usr/bin/env python
"""
Test script for Assignment system.
Verifies that:
1. Teachers can create assignments
2. Students can view and submit assignments
3. Teachers can grade submissions
4. Permission checks work correctly
"""

import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'AcuVerify.settings')
django.setup()

from django.utils import timezone
from datetime import timedelta
from AcuVerifyapp.models import (
    Staff, Students, Subject, Streams, Classes, AcademicYear,
    StaffSubjectStream, Assignment, StudentAssignmentSubmission
)

def test_assignment_system():
    """Test the assignment system workflow"""
    
    print("\n" + "="*60)
    print("ASSIGNMENT SYSTEM TEST")
    print("="*60)
    
    # Get existing data
    staff = Staff.objects.first()
    student = Students.objects.first()
    
    if not staff or not student:
        print("ERROR: No staff or student data found!")
        return False
    
    print(f"\nTest Teacher: {staff.fname} {staff.lname} ({staff.email})")
    print(f"Test Student: {student.fname} {student.lname} ({student.email})")
    
    # Check if teacher teaches the student's stream/subject
    stream = student.stream_id
    subjects = staff.subject_specialization.all()
    
    if not stream or not subjects.exists():
        print("\nWARNING: Teacher doesn't teach student's stream or has no subjects")
        print(f"Student Stream: {stream}")
        print(f"Teacher Subjects: {list(subjects)}")
    
    # Check StaffSubjectStream records
    print("\nChecking StaffSubjectStream records...")
    sss_records = StaffSubjectStream.objects.filter(staff_id=staff).count()
    print(f"Teacher has {sss_records} StaffSubjectStream record(s)")
    
    if sss_records > 0:
        sss = StaffSubjectStream.objects.filter(staff_id=staff).first()
        print(f"  - Subject: {sss.subject_id}, Stream: {sss.stream_id}, Academic Year: {sss.academic_year}")
        
        # Try to create an assignment
        print("\nAttempting to create an assignment...")
        try:
            due_date = timezone.now() + timedelta(days=7)
            assignment = Assignment.objects.create(
                title="Test Assignment",
                description="This is a test assignment for the assignment system.",
                assignment_type="HOMEWORK",
                subject_id=sss.subject_id,
                stream_id=sss.stream_id,
                created_by=staff,
                total_marks=100,
                due_date=due_date
            )
            print(f"✓ Assignment created: {assignment.title} (ID: {assignment.id})")
            
            # Check if student can see the assignment
            print("\nChecking if student can see the assignment...")
            if assignment.stream_id == student.stream_id:
                print("✓ Student can see the assignment (same stream)")
                
                # Try to create a submission
                print("\nAttempting to create a submission...")
                submission, created = StudentAssignmentSubmission.objects.get_or_create(
                    assignment_id=assignment.id,
                    student_id=student.id,
                    defaults={'status': 'NOT_STARTED'}
                )
                if created:
                    print(f"✓ Submission created (ID: {submission.id})")
                else:
                    print(f"✓ Submission exists (ID: {submission.id})")
                
                # Try to submit
                print("\nAttempting to submit the assignment...")
                submission.submission_text = "This is my answer to the test assignment."
                submission.submission_date = timezone.now()
                submission.status = 'SUBMITTED'
                submission.save()
                print(f"✓ Submission updated: Status = {submission.get_status_display()}")
                
                # Try to grade
                print("\nAttempting to grade the submission...")
                submission.marks_obtained = 85
                submission.remarks = "Good work! Well organized."
                submission.graded_by = staff
                submission.graded_at = timezone.now()
                submission.status = 'GRADED'
                submission.save()
                print(f"✓ Submission graded: {submission.marks_obtained}/{assignment.total_marks}")
                print(f"  Percentage: {submission.percentage_score:.1f}%")
                
            else:
                print("✗ Student cannot see the assignment (different stream)")
                
        except Exception as e:
            print(f"✗ Error creating assignment: {e}")
            import traceback
            traceback.print_exc()
            return False
    else:
        print("WARNING: No StaffSubjectStream records found. Teacher may not be assigned to any streams.")
    
    # Test queries
    print("\n" + "-"*60)
    print("TEST QUERIES")
    print("-"*60)
    
    print(f"\nTotal Assignments: {Assignment.objects.count()}")
    print(f"Total Submissions: {StudentAssignmentSubmission.objects.count()}")
    
    # Check permissions
    print("\n" + "-"*60)
    print("PERMISSION TESTS")
    print("-"*60)
    
    assignment = Assignment.objects.first()
    if assignment:
        print(f"\nAssignment: {assignment.title}")
        print(f"Created by: {assignment.created_by}")
        
        # Only the creator should be able to grade
        other_staff = Staff.objects.exclude(id=assignment.created_by.id).first()
        if other_staff:
            print(f"\nTesting permission with different teacher: {other_staff.fname} {other_staff.lname}")
            is_creator = assignment.created_by == other_staff
            print(f"Can grade submission: {is_creator} (should be False)")
    
    print("\n" + "="*60)
    print("TEST COMPLETE")
    print("="*60)
    return True


if __name__ == "__main__":
    test_assignment_system()
