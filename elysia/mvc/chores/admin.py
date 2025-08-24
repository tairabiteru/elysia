from django.contrib import admin

from .models import Chore, Assignment, Accomplishment, Notification


admin.site.register(Chore)
admin.site.register(Assignment)
admin.site.register(Accomplishment)
admin.site.register(Notification)
