from django.contrib import admin

# Register your models here.
from .models import Staff, Subject, Classes, Students, Streams

admin.site.register(Staff)
admin.site.register(Subject)
admin.site.register(Classes)
admin.site.register(Students)
admin.site.register(Streams)