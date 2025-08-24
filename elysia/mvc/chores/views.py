from django.http import HttpRequest, HttpResponse

from ..core.utils import template
from ..core.oauth2 import require_auth
from .models import Chore, get_split_chores, Accomplishment
from ..discord.models import User


@require_auth
@template("chores.html")
async def chores(request: HttpRequest) -> dict:
    return {}


@require_auth
@template("chores_enum.html")
async def get_chores(request: HttpRequest) -> dict:
    uid = request.session.get("uid")
    user = await User.objects.aget(id=uid)
    unfinished, finished = await get_split_chores(user)
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
