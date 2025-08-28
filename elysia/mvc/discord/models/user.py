import datetime
from django.db import models
import typing as t

from .base import DiscordBaseModel
from ...core.fields import TimezoneField
from ..fields import UserIDField
from ....lib.permissions import PermissionState


epoch = datetime.datetime(year=1970, month=1, day=1, hour=0, minute=0, second=0)


class User(DiscordBaseModel):
    id = UserIDField(primary_key=True, help_text="The Discord ID of this user.")
    acl = models.ManyToManyField("discord.PermissionsObject", blank=True, help_text="The Access Control List of this user, determining their permissions.")
    _name = models.CharField(max_length=128, unique=True, blank=True, null=True)
    chore_daemon = models.BooleanField(default=False)
    notify_times = models.TextField(default="", blank=True)
    last_notify = models.DateTimeField(default=epoch)
    timezone = TimezoneField()

    @property
    def obj(self):
        try:
            if self._resolved['id'] is None:
                return None
            if isinstance(self._resolved['id'], Exception):
                raise self._resolved['id']
            return self._resolved['id']
        except KeyError:
            raise ValueError("resolve_all() must be called before accessing.")
    
    async def get_acl(self, root):
        acl = {}
        async for obj in self.acl.all():
            node = root.get_node(obj.node)
            setting = PermissionState.DENY if obj.setting == "-" else PermissionState.ALLOW
            acl[node] = setting
        return acl 
    
    def __str__(self):
        if self._name:
            return self._name
        try:
            return f"{self.obj.username}#{self.obj.discriminator}"
        except ValueError: 
            return f"UID: {self.id}"
        except AttributeError:
            return f"UID: {self.id} (Not in cache)"
    
    async def fetch_acl(self):
        acl = {}
        async for obj in self.acl.all():
            acl[obj.node] = obj.setting
        return acl