from django.urls import path

from .views import chores, get_chores, accomplish


urlpatterns = [
    path("", chores),
    path("all", get_chores),
    path("<int:chore_id>/accomplish", accomplish)
]
