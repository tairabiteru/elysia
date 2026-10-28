import datetime
from django.db import models
import hikari
import oronyx
import zoneinfo

from ...discord.models import DiscordBaseModel
from ....core.conf import Config
from ....lib.utils import get_approx_timedelta, utcnow


conf = Config.load()


class Task(DiscordBaseModel):
    id = models.AutoField(primary_key=True)
    name = models.TextField()
    notify = models.CharField(max_length=256)
    utc_due_date = models.DateTimeField()
    accomplished = models.BooleanField(default=False)
    user = models.ForeignKey("discord.User", on_delete=models.CASCADE)
    utc_creation_date = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return self.name
    
    @property
    def due_date(self) -> datetime.datetime:
        return self.utc_due_date.astimezone(zoneinfo.ZoneInfo(self.user.timezone))
    
    @property
    def creation_date(self) -> datetime.datetime:
        return self.utc_creation_date.astimezone(zoneinfo.ZoneInfo(self.user.timezone))
    
    @property
    def notify_after(self) -> datetime.datetime:
        return oronyx.get_past(self.due_date, self.notify)
    
    @property
    def utc_notify_after(self) -> datetime.datetime:
        return oronyx.get_past(self.utc_due_date, self.notify)
    
    def get_timedelta_display(self, now: datetime.datetime) -> str:
        delta = self.due_date - now
        delta = get_approx_timedelta(delta)
        if self.due_date > now:
            return f"{delta} from now"
        else:
            return f"{delta} ago"
    
    @property
    def is_later(self) -> bool:
        return utcnow() < self.utc_notify_after
    
    async def prefetch(self, bot: hikari.GatewayBot) -> Task:
        self = await Task.objects.select_related("user").aget(id=self.id)
        self.user.attach_bot(bot)
        await self.user.aresolve_all()
        return self
    
    def get_embed(self) -> hikari.Embed:
        e = hikari.Embed(title="Task!")
        e.description = self.name
        e.set_thumbnail("https://cdn-icons-png.flaticon.com/512/6783/6783643.png")
        return e
    
    async def process(self, bot: hikari.GatewayBot, utcnow: datetime.datetime) -> None:
        await self.prefetch(bot)

        if utcnow >= self.notify_after:
            await self.user.obj.send(embed=self.get_embed()) # type: ignore

        self.accomplished = True
        await self.asave()