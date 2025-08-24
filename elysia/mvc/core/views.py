from asgiref.sync import sync_to_async
from django.shortcuts import redirect

from ...core.conf import Config
from ..core.oauth2 import decrypt_state
from .utils import template


conf = Config.load()


async def auth(request):
    state = request.GET.get('state')
    state = decrypt_state(state)
    code = request.GET.get('code')
    return redirect(f"{state['redirect']}?code={code}")


@template("index.html")
async def index(request):
    authenticated = await sync_to_async(lambda: request.user.is_authenticated)()
    uid = request.session.get("uid", None)
    return {
        'avatar_url': request.bot.get_me().make_avatar_url(),
        'name': request.bot.get_me().username,
        'version': f"v{request.bot.conf.version} '{request.bot.conf.version_tag}'",
        'display_admin': authenticated or uid == conf.owner_id
    }