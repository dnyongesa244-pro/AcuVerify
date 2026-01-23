from django.contrib import admin, messages
from django.urls import path
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django import forms
from django.contrib.admin.widgets import FilteredSelectMultiple

from .models import Staff, Subject, Classes, Students, Streams, Assignment, StudentAssignmentSubmission, StaffSubjectStream


class BulkAssignClassForm(forms.Form):
	target_class = forms.ModelChoiceField(queryset=Classes.objects.all(), label='Class to assign')
	subjects = forms.ModelMultipleChoiceField(
		queryset=Subject.objects.all(),
		required=False,
		widget=FilteredSelectMultiple('Subjects', is_stacked=False)
	)


class BulkRemoveClassForm(forms.Form):
    target_class = forms.ModelChoiceField(queryset=Classes.objects.all(), label='Class to remove')
    subjects = forms.ModelMultipleChoiceField(
        queryset=Subject.objects.all(),
        required=False,
        widget=FilteredSelectMultiple('Subjects', is_stacked=False)
    )


class SubjectAdmin(admin.ModelAdmin):
	list_display = ('subject_name', 'get_classes')
	search_fields = ('subject_name',)
	filter_horizontal = ('classes',)

	def get_classes(self, obj):
		return ", ".join([c.class_name for c in obj.classes.all()])
	get_classes.short_description = 'Classes'

	def get_urls(self):
		urls = super().get_urls()
		custom_urls = [
			path('bulk-assign-class/', self.admin_site.admin_view(self.bulk_assign_class_view), name='subject_bulk_assign_class'),
			path('bulk-remove-class/', self.admin_site.admin_view(self.bulk_remove_class_view), name='subject_bulk_remove_class'),
		]
		return custom_urls + urls

	def bulk_assign_class_view(self, request):
		"""Custom admin view to bulk assign a selected class to chosen subjects.

		GET: show a simple form to choose a class and subjects
		POST: attach the chosen class to the selected subjects (adds to M2M)
		"""
		if request.method == 'POST':
			form = BulkAssignClassForm(request.POST)
			if form.is_valid():
				target = form.cleaned_data['target_class']
				subjects = form.cleaned_data['subjects']
				count = 0
				for subj in subjects:
					subj.classes.add(target)
					count += 1
				messages.success(request, f'Assigned class "{target.class_name}" to {count} subject(s).')
				return redirect('..')
		else:
			form = BulkAssignClassForm()

		context = dict(
			self.admin_site.each_context(request),
			title='Bulk assign class to subjects',
			form=form,
		)
		return TemplateResponse(request, 'admin/bulk_assign_class.html', context)

	def bulk_remove_class_view(self, request):
		"""Custom admin view to bulk remove a selected class from chosen subjects.

		GET: show a simple form to choose a class and subjects
		POST: remove the chosen class from the selected subjects (M2M remove)
		"""
		if request.method == 'POST':
			form = BulkRemoveClassForm(request.POST)
			if form.is_valid():
				target = form.cleaned_data['target_class']
				subjects = form.cleaned_data['subjects']
				count = 0
				for subj in subjects:
					subj.classes.remove(target)
					count += 1
				messages.success(request, f'Removed class "{target.class_name}" from {count} subject(s).')
				return redirect('..')
		else:
			form = BulkRemoveClassForm()

		context = dict(
			self.admin_site.each_context(request),
			title='Bulk remove class from subjects',
			form=form,
		)
		return TemplateResponse(request, 'admin/bulk_assign_class.html', context)


class AssignmentAdmin(admin.ModelAdmin):
	list_display = ('title', 'subject_id', 'stream_id', 'created_by', 'due_date', 'is_active')
	list_filter = ('is_active', 'created_at', 'due_date', 'assignment_type')
	search_fields = ('title', 'description')
	readonly_fields = ('created_at', 'updated_at')
	fields = ('title', 'description', 'assignment_type', 'subject_id', 'stream_id', 'created_by', 'total_marks', 'due_date', 'assignment_file', 'is_active', 'created_at', 'updated_at')

	def save_model(self, request, obj, form, change):
		if not change:
			obj.created_by = request.user if hasattr(request.user, 'staff') else Staff.objects.filter(email=request.user.email).first()
		super().save_model(request, obj, form, change)


class StudentAssignmentSubmissionAdmin(admin.ModelAdmin):
	list_display = ('student_id', 'assignment_id', 'status', 'submission_date', 'marks_obtained')
	list_filter = ('status', 'submission_date', 'graded_at')
	search_fields = ('student_id__fname', 'student_id__lname', 'assignment_id__title')
	readonly_fields = ('created_at', 'updated_at', 'submission_date')
	fields = ('assignment_id', 'student_id', 'status', 'submission_file', 'submission_text', 'submission_date', 'marks_obtained', 'remarks', 'graded_by', 'graded_at', 'created_at', 'updated_at')

	def has_add_permission(self, request):
		return False


admin.site.register(Staff)
admin.site.register(Subject, SubjectAdmin)
admin.site.register(Classes)
admin.site.register(Students)
admin.site.register(Streams)
admin.site.register(Assignment, AssignmentAdmin)
admin.site.register(StudentAssignmentSubmission, StudentAssignmentSubmissionAdmin)
admin.site.register(StaffSubjectStream)