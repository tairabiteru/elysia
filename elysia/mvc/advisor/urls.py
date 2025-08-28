from django.urls import path

from .views import chores, get_chores, accomplish, reminders, get_reminders, toggle_recurring, delete_reminder, create_reminder, oronyx_eval


urlpatterns = [
    path("reminders", reminders),
    path("reminders/all", get_reminders),
    path("reminders/<int:reminder_id>/alter/toggle_recurring", toggle_recurring),
    path("reminders/<int:reminder_id>/alter/delete", delete_reminder),
    path("reminders/create", create_reminder),
    
    path("chores", chores),
    path("chores/all", get_chores),
    path("chores/<int:chore_id>/accomplish", accomplish),

    path("eval_time_string", oronyx_eval)
]
