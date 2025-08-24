from django.db import models
import random

from ..core.models import BaseAsyncModel


class PartOfSpeech(BaseAsyncModel):
    class Type(models.IntegerChoices):
        VERB = 0
        DIRECT_OBJECT = 1

    type = models.IntegerField(choices=Type.choices)
    value = models.CharField(max_length=128)


    def __str__(self) -> str:
        return f"{self.Type(self.type).label}: {self.value}"


async def aget_threat() -> str:
    verbs = []
    async for verb in PartOfSpeech.objects.filter(
        type=PartOfSpeech.Type.VERB
    ):
        verbs.append(verb)
    
    objects = []
    async for object in PartOfSpeech.objects.filter(
        type=PartOfSpeech.Type.DIRECT_OBJECT
    ):
        objects.append(object)
    
    verb = random.choice(verbs)
    obj = random.choice(objects)
    return f"or else I will {verb.value} {obj.value}."
        
