from __future__ import annotations
import datetime
from django.db import models
from django.utils import timezone
import hikari
import oronyx
import typing as t

from ...core.models import BaseAsyncModel
from ...discord.models import DiscordBaseModel
from ....core.conf import Config
from ....lib.utils import get_approx_timedelta


conf = Config.load()


class Chore(DiscordBaseModel):
    name = models.CharField(unique=True, max_length=128)
    frequency = models.CharField(max_length=256)
    accomplishments = models.ManyToManyField("Accomplishment", blank=True)
    assign_to = models.ForeignKey("discord.User", default=None, null=True, blank=True, on_delete=models.SET_DEFAULT)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._last_accomplishment: int | None | datetime.datetime = 0

    def __str__(self) -> str:
        return self.name
    
    @property
    def last_accomplishment(self) -> datetime.datetime:
        if self._last_accomplishment != 0:
            return self._last_accomplishment # type: ignore
        raise RuntimeError("prefetch not called.")
    
    @property
    def last_acc_shorthand(self) -> str:
        now = timezone.localtime()
        delta = now - self.last_accomplishment
        return get_approx_timedelta(delta)

    def get_last_accomplishment(self) -> t.Optional[datetime.datetime]:
        try:
            latest = self.accomplishments.latest("utc_timestamp")
        except Accomplishment.DoesNotExist:
            return None
        return latest.timestamp
    
    async def aget_last_accomplishment(self) -> t.Optional[datetime.datetime]:
        try:
            latest = await self.accomplishments.alatest("utc_timestamp")
        except Accomplishment.DoesNotExist:
            return None
        return latest.timestamp
    
    def needs_doing(self) -> bool:
        last = self.get_last_accomplishment()
        if not last:
            return True
        future = oronyx.get_future(last, self.frequency)
        return timezone.localtime() > future
    
    async def aneeds_doing(self) -> bool:
        last = await self.aget_last_accomplishment()
        if not last:
            return True
        
        future = oronyx.get_future(last, self.frequency)
        return timezone.localtime() > future
    
    async def prefetch(self) -> None:
        self._last_accomplishment = await self.aget_last_accomplishment()

    @classmethod
    async def get_split_chores(cls, user) -> t.Tuple[t.List[Chore], t.List[Chore]]:
        finished = []
        unfinished = []

        async for chore in cls.objects.filter(assign_to=user):
            await chore.prefetch()

            if await chore.aneeds_doing():    
                unfinished.append(chore)
            else:
                finished.append(chore)

        return unfinished, finished
    
    @staticmethod
    def get_embed(chores: t.List[Chore], threat: str | None=None) -> hikari.Embed:
        embed = hikari.Embed(title="Chores Reminder")
        embed.description = "These are the current chores which still need to be done."
        if threat is not None:
            embed.description += f" You better do them {threat}"
        embed.url = f"https://{conf.mvc.allowed_hosts[0]}/advisor/chores"

        for chore in chores:
            embed.add_field(name=chore.name, value=chore.frequency)
        return embed


class Accomplishment(BaseAsyncModel):
    user = models.ForeignKey("discord.User", on_delete=models.CASCADE)
    utc_timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.user} accomplished at {self.timestamp}"
    
    @property
    def timestamp(self) -> datetime.datetime:
        return self.utc_timestamp.astimezone(conf.timezone)


class Notification(BaseAsyncModel):
    user = models.ForeignKey("discord.User", on_delete=models.CASCADE)
    utc_timestamp = models.DateTimeField(auto_now_add=True)
    message_id = models.BigIntegerField()
    chores = models.ManyToManyField("Chore")

    def __str__(self) -> str:
        return f"{self.user} notified at {self.timestamp}"
    
    @property
    def timestamp(self) -> datetime.datetime:
        return self.utc_timestamp.astimezone(conf.timezone)
