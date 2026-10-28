from django.urls import path

from .views import oronyx_eval
from .views import chores, get_chores, accomplish
from .views import reminders, get_reminders, toggle_recurring, delete_reminder, create_reminder
from .views import tasks, get_tasks, delete_task, create_task


urlpatterns = [
    path("reminders", reminders),
    path("reminders/all", get_reminders),
    path("reminders/<int:reminder_id>/alter/toggle_recurring", toggle_recurring),
    path("reminders/<int:reminder_id>/alter/delete", delete_reminder),
    path("reminders/create", create_reminder),
    
    path("tasks", tasks),
    path("tasks/all", get_tasks),
    path("tasks/<int:task_id>/alter/delete", delete_task),
    path("tasks/create", create_task),
    
    path("chores", chores),
    path("chores/all", get_chores),
    path("chores/<int:chore_id>/accomplish", accomplish),

    path("eval_time_string", oronyx_eval)
]
