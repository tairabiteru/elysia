from __future__ import annotations
import datetime
from django.db import models
from django.utils import timezone
import hikari
import oronyx
import zoneinfo

from ...discord.models import DiscordBaseModel
from ....core.conf import Config


conf = Config.load()


class Reminder(DiscordBaseModel):
    user = models.ForeignKey("discord.User", on_delete=models.CASCADE)
    rule = models.CharField(max_length=256)
    utc_last_notify = models.DateTimeField(default=None, null=True, blank=True)
    recurring = models.BooleanField(default=False)
    text = models.TextField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._timezone: zoneinfo.ZoneInfo | None = None

    def save(self, *args, **kwargs):
        if self.utc_last_notify is None:
            self.utc_last_notify = timezone.localtime()
        return super().save(*args, *kwargs)
    
    async def asave(self, *args, **kwargs):
        if self.utc_last_notify is None:
            self.utc_last_notify = timezone.localtime()
        return await super().asave(*args, **kwargs)
    
    @property
    def timezone(self) -> zoneinfo.ZoneInfo:
        if self._timezone is not None:
            return self._timezone
        raise RuntimeError("Prefetch not called.")

    def get_embed(self) -> hikari.Embed:
        e = hikari.Embed(title="Reminder!")
        e.description = self.text
        e.set_thumbnail("https://storage.needpix.com/rsynced_images/clock-2690491_1280.png")

        if self.recurring is True:
            e.add_field("Next Reminder", self.future)

        return e
    
    @property
    def future(self) -> datetime.datetime:
        return oronyx.get_future(self.local_last_notify, self.rule)
    
    @property
    def local_last_notify(self) -> datetime.datetime:
        return self.utc_last_notify.astimezone(zoneinfo.ZoneInfo(self.timezone))
    
    async def prefetch(self) -> Reminder:
        r = await Reminder.objects.select_related("user").aget(id=self.id)
        self._timezone = r.user.timezone
        self.user = r.user
        return self
    
    async def process(self, bot: hikari.GatewayBot, utcnow: datetime.datetime):
        await self.prefetch()

        if utcnow >= self.future:
            self.user.attach_bot(bot)
            await self.user.aresolve_all()

            self.utc_last_notify = utcnow
            await self.user.obj.send(embed = self.get_embed())

            if self.recurring is False:
                await self.adelete()
            else:
                await self.asave()