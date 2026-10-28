from django.contrib import admin

from .models import Chore, Accomplishment, Notification, Reminder, Task


admin.site.register(Chore)
admin.site.register(Accomplishment)
admin.site.register(Notification)
admin.site.register(Reminder)
admin.site.register(Task)
