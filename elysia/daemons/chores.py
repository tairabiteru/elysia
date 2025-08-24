from asgiref.sync import sync_to_async
from django.utils import timezone
import hikari
import nintab
import typing as t

from ..lib.daemon import daemon
from ..core.log import logging
from ..core.conf import Config
from ..mvc.chores.models import get_split_chores, Notification, ChoresEmbed
from ..mvc.discord.models import User
from ..mvc.threats.models import aget_threat

conf = Config.load()
logger = logging.getLogger(conf.name).getChild("daemons")


@daemon("chore", seconds=1)
async def chore_daemon(bot: hikari.GatewayBot) -> None:
    now = timezone.localtime()
    now = now.replace(microsecond=0)

    async for user in User.objects.filter(chore_daemon=True):
        notify_times = user.notify_times.split(",")
        for time in notify_times:
            last = user.last_notify.astimezone(timezone.get_current_timezone())
            future = nintab.get_future(time, now=last)

            if future < now:
                unfinished, _ = await get_split_chores(user)
                
                if any(unfinished):
                    threat = await aget_threat()
                    embed = ChoresEmbed(unfinished, threat=threat)
                    await user.aresolve_all(bot)
                    message = await user.obj.send(embed=embed)
                    
                    if message.id:

                        notification = Notification(user=user, message_id=message.id)
                        await notification.asave()
                        for chore in unfinished:
                            await notification.chores.aadd(chore)

                        user.last_notify = notification.timestamp
                        await user.asave()
