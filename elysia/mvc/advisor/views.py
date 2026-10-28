import datetime
from django.http import HttpRequest, HttpResponse
import oronyx
import zoneinfo

from ..core.utils import template
from ..core.oauth2 import require_auth
from .models import Chore, Accomplishment, Reminder, Task
from ..discord.models import User


async def oronyx_eval(request: HttpRequest) -> HttpResponse:
    rule = request.POST['rule']
    eval_type = request.POST['eval_type']
    
    if eval_type == "timeline":
        out = oronyx.get_blank_timeline(rule)
    elif eval_type == "future":
        out = oronyx.get_future_obj(rule)
    elif eval_type == "past":
        out = oronyx.get_past_obj(rule)
    else:
        raise ValueError(f"eval_type must be one of 'future', 'past', or 'timeline'.")
    
    if out:
        return HttpResponse("OK")
    else:
        return HttpResponse("null")


@require_auth
@template("chores.html")
async def chores(request: HttpRequest) -> dict:
    uid = request.session['uid']
    user, _ = await User.objects.aget_or_create(id=uid)
    user.attach_bot(request.bot) # type: ignore
    await user.aresolve_all()
    return {'avatar_url': user.obj.display_avatar_url} # type: ignore


@require_auth
@template("chores_enum.html")
async def get_chores(request: HttpRequest) -> dict:
    uid = request.session.get("uid")
    user = await User.objects.aget(id=uid)
    unfinished, finished = await Chore.get_split_chores(user)
    return {'unfinished': unfinished, 'finished': finished}


@require_auth
async def accomplish(request: HttpRequest, chore_id: int) -> HttpResponse:
    uid = request.session.get("uid")
    user = await User.objects.aget(id=uid)
    chore = await Chore.objects.aget(id=chore_id)

    accomplishment = Accomplishment(user=user)
    await accomplishment.asave()
    await chore.accomplishments.aadd(accomplishment)

    return await get_chores(request) # type: ignore


@require_auth
@template("reminders.html")
async def reminders(request: HttpRequest) -> dict:
    uid = request.session['uid']
    user, _ = await User.objects.aget_or_create(id=uid)
    user.attach_bot(request.bot) # type: ignore
    await user.aresolve_all()

    return {'avatar_url': user.obj.display_avatar_url} # type: ignore


@require_auth
@template("reminders_enum.html")
async def get_reminders(request: HttpRequest) -> dict:
    uid = request.session.get("uid")
    user = await User.objects.aget(id=uid)
    
    reminders = []
    async for reminder in Reminder.objects.filter(user=user):
        reminders.append(reminder)

    return {'reminders': reminders}


@require_auth
async def toggle_recurring(request: HttpRequest, reminder_id: int) -> dict:
    reminder = await Reminder.objects.aget(id=reminder_id)
    reminder.recurring = not reminder.recurring
    await reminder.asave()

    return await get_reminders(request)


@require_auth
async def delete_reminder(request: HttpRequest, reminder_id: int) -> dict:
    reminder = await Reminder.objects.aget(id=reminder_id)
    await reminder.adelete()

    return await get_reminders(request)


@require_auth
async def create_reminder(request: HttpRequest) -> dict:
    uid = request.session.get("uid")
    user = await User.objects.aget(id=uid)
    
    rule = request.POST['rule']
    text = request.POST['text']
    reminder = Reminder(
        rule=rule,
        text=text,
        user=user
    )

    await reminder.asave()
    return await get_reminders(request)


@require_auth
@template("tasks.html")
async def tasks(request: HttpRequest) -> dict:
    uid = request.session['uid']
    user, _ = await User.objects.aget_or_create(id=uid)
    user.attach_bot(request.bot) # type: ignore
    await user.aresolve_all()

    return {'avatar_url': user.obj.display_avatar_url} # type: ignore


@require_auth
@template("tasks_enum.html")
async def get_tasks(request: HttpRequest) -> dict:
    uid = request.session.get("uid")
    user = await User.objects.aget(id=uid)
    
    tasks = []
    later_tasks = []
    async for task in Task.objects.filter(user=user):
        if task.is_later:
            later_tasks.append(task)
        else:
            tasks.append(task)

    return {'tasks': tasks, 'later_tasks': later_tasks}


@require_auth
async def delete_task(request: HttpRequest, task_id: int) -> dict:
    task = await Task.objects.aget(id=task_id)
    await task.adelete()

    return await get_tasks(request)


@require_auth
async def create_task(request: HttpRequest) -> dict:
    uid = request.session.get("uid")
    user = await User.objects.aget(id=uid)
    
    name = request.POST['text']
    notify = request.POST['rule']
    due_date = request.POST['due_date']
    due_time = request.POST['due_time'] if request.POST['due_time'] else "00:00"
    
    utc_due_date = datetime.datetime.strptime(
        f"{due_date}T{due_time}",
        "%Y-%m-%dT%H:%M"
    )
    utc_due_date = utc_due_date.replace(tzinfo=zoneinfo.ZoneInfo(user.timezone))
    utc_due_date = utc_due_date.astimezone(zoneinfo.ZoneInfo("UTC"))
    
    task = Task(
        user=user,
        name=name,
        notify=notify,
        utc_due_date=utc_due_date
    )

    await task.asave()
    return await get_tasks(request)

