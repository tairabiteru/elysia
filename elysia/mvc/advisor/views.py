from django.http import HttpRequest, HttpResponse
import oronyx

from ..core.utils import template
from ..core.oauth2 import require_auth
from .models import Chore, Accomplishment, Reminder
from ..discord.models import User


async def oronyx_eval(request: HttpRequest) -> HttpResponse:
    rule = request.POST['rule']
    scheduler = oronyx.get_scheduler(rule)
    if scheduler:
        return HttpResponse(scheduler.regex)
    else:
        return HttpResponse("null")


@require_auth
@template("chores.html")
async def chores(request: HttpRequest) -> dict:
    uid = request.session['uid']
    user, _ = await User.objects.aget_or_create(id=uid)
    user.attach_bot(request.bot) # type: ignore
    await user.aresolve_all()
    return {'avatar_url': user.obj.avatar_url} # type: ignore


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
    return {'avatar_url': user.obj.avatar_url} # type: ignore


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
async def toggle_recurring(request: HttpRequest, reminder_id: int) -> HttpResponse:
    reminder = await Reminder.objects.aget(id=reminder_id)
    reminder.recurring = not reminder.recurring
    await reminder.asave()

    return await get_reminders(request)


@require_auth
async def delete_reminder(request: HttpRequest, reminder_id: int) -> HttpResponse:
    reminder = await Reminder.objects.aget(id=reminder_id)
    await reminder.adelete()

    return await get_reminders(request)


@require_auth
async def create_reminder(request: HttpRequest) -> HttpResponse:
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

