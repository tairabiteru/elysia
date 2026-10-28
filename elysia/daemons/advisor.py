import asyncio
from django.utils import timezone
import hikari
import oronyx
import zoneinfo


from ..lib.daemon import daemon
from ..core.log import logging
from ..core.conf import Config
from ..mvc.advisor.models import Notification, Chore, Reminder, Task
from ..mvc.discord.models import User
from ..mvc.threats.models import aget_threat


conf = Config.load()
logger = logging.getLogger(conf.name).getChild("daemons")

chore_lock = asyncio.Lock()
reminder_lock = asyncio.Lock()
task_lock = asyncio.Lock()


@daemon("chore", seconds=0.2)
async def chore_daemon(bot: hikari.GatewayBot) -> None:
    now = timezone.localtime()
    now = now.replace(microsecond=0)

    async for user in User.objects.filter(chore_daemon=True):
        notify_times = user.notify_times.split(",")
        
        if not any(notify_times):
            continue

        for time in notify_times:
            last = user.last_notify.astimezone(timezone.get_current_timezone())
            timeline = oronyx.get_timeline(last, time)

            if timeline[0] < now:
                unfinished, _ = await Chore.get_split_chores(user)
                # tasks = await Task.get_unfinished(user)

                if any(unfinished) or any(tasks):
                    async with chore_lock:
                        threat = await aget_threat()
                        embed = Chore.get_embed(unfinished, threat=threat)
                        await user.aresolve_all(bot)
                        message = await user.obj.send(embed=embed) # type: ignore
                        
                        if message.id:
                            notification = Notification(user=user, message_id=message.id)
                            await notification.asave()
                            for chore in unfinished:
                                await notification.chores.aadd(chore)

                            user.last_notify = notification.timestamp
                            await user.asave()


@daemon("reminder", seconds=0.2)
async def reminder_daemon(bot: hikari.GatewayBot) -> None:
    utcnow = timezone.localtime().astimezone(zoneinfo.ZoneInfo("UTC"))
    utcnow = utcnow.replace(microsecond=0)

    async for reminder in Reminder.objects.all():
        async with reminder_lock:
            await reminder.process(bot, utcnow)


@daemon("tasks", seconds=0.2)
async def tasks_daemon(bot: hikari.GatewayBot) -> None:
    utcnow = timezone.localtime().astimezone(zoneinfo.ZoneInfo("UTC"))
    utcnow = utcnow.replace(microsecond=0)
    
    async for task in Task.objects.all():
        async with task_lock:
            await task.prefetch(bot)
            
            
            

    