import datetime
from django.db import models
from django.utils import timezone
import hikari
import nintab
import typing as t

from ..core.models import BaseAsyncModel
from ..discord.models import DiscordBaseModel
from ...core.conf import Config


conf = Config.load()


class Chore(BaseAsyncModel):
    name = models.CharField(unique=True, max_length=128)
    frequency = models.CharField(max_length=256)
    accomplishments = models.ManyToManyField("Accomplishment", blank=True)

    def __str__(self) -> str:
        return self.name
    
    def get_last_accomplishment(self) -> t.Optional[datetime.datetime]:
        try:
            latest = self.accomplishments.latest("timestamp")
        except Accomplishment.DoesNotExist:
            return None
        return latest.timestamp
    
    async def aget_last_accomplishment(self) -> t.Optional[datetime.datetime]:
        try:
            latest = await self.accomplishments.alatest("timestamp")
        except Accomplishment.DoesNotExist:
            return None
        return latest.timestamp
    
    def needs_doing(self) -> bool:
        last = self.get_last_accomplishment()
        if not last:
            return True
        future = nintab.get_future(self.frequency, now=last)
        return timezone.localtime() > future
    
    async def aneeds_doing(self) -> bool:
        last = await self.aget_last_accomplishment()
        if not last:
            return True
        future = nintab.get_future(self.frequency, now=last)
        return timezone.localtime() > future


class Assignment(DiscordBaseModel):
    chore = models.ForeignKey("Chore", on_delete=models.CASCADE)
    user = models.ForeignKey("discord.User", on_delete=models.CASCADE)

    def __str__(self) -> str:
        return f"{self.chore} assigned to {self.user}"


class Accomplishment(BaseAsyncModel):
    user = models.ForeignKey("discord.User", on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.user} accomplished at {self.timestamp}"


class Notification(BaseAsyncModel):
    user = models.ForeignKey("discord.User", on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    message_id = models.BigIntegerField()
    chores = models.ManyToManyField("Chore")

    def __str__(self) -> str:
        return f"{self.user} notified at {self.timestamp}"


class ChoresEmbed(hikari.Embed):
    def __init__(self, chores: t.List[Chore], threat: str):
        self.chores = chores
        super().__init__(title="Chores Reminder")
        self.description = f"These are the current chores which still need to be done. You better do them {threat}"
        self.url = f"https://{conf.mvc.allowed_hosts[0]}/chores"


        for chore in self.chores:
            self.add_field(name=chore.name, value=chore.frequency)
        



async def get_split_chores(user) -> t.Tuple[t.List[Chore], t.List[Chore]]:
    finished = []
    unfinished = []

    async for assignment in Assignment.objects.filter(user=user):
        chore = await Chore.objects.aget(assignment=assignment)
        if await chore.aneeds_doing():
            unfinished.append(chore)
        else:
            finished.append(chore)
    
    return unfinished, finished