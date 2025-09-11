from __future__ import annotations
import datetime
from django.db import models
import hikari
import zoneinfo

from ...discord.models import DiscordBaseModel
from ....core.conf import Config
from ....lib.utils import get_approx_timedelta


conf = Config.load()


class Task(DiscordBaseModel):
    name = models.TextField()
    notify = models.CharField(max_length=256)
    utc_due_date = models.DateTimeField()
    accomplished = models.BooleanField(default=False)
    assigned_to = models.ForeignKey("discord.User", default=None, null=True, blank=True, on_delete=models.SET_DEFAULT)
    utc_creation_date = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return self.name
    
    @property
    def due_date(self) -> datetime.datetime:
        return self.utc_due_date.astimezone(zoneinfo.ZoneInfo(self.assigned_to.timezone))
    
    @property
    def creation_date(self) -> datetime.datetime:
        return self.utc_creation_date.astimezone(zoneinfo.ZoneInfo(self.assigned_to.timezone))
    
    @property
    def notify_after(self) -> datetime.datetime:
        ...
    
    def get_timedelta_display(self, now: datetime.datetime) -> str:
        delta = self.due_date - now
        delta = get_approx_timedelta(delta)
        if self.due_date > now:
            return f"{delta} from now"
        else:
            return f"{delta} ago"
    
    async def prefetch(self, bot: hikari.GatewayBot) -> Task:
        self = await Task.objects.select_related("assigned_to").aget(id=self.id)
        self.assigned_to.attach_bot(bot)
        await self.assigned_to.aresolve_all()
        return self