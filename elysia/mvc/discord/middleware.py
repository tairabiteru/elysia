import asyncio
import hikari
from django.utils.decorators import sync_and_async_middleware


@sync_and_async_middleware
def BotInjectorMiddleware(get_response):
    loop = asyncio.get_running_loop()

    if asyncio.iscoroutinefunction(get_response):
        async def middleware(request):
            request.bot: hikari.GatewayBot = loop.bot
            return await get_response(request)
    else:
        def middleware(request):
            request.bot: hikari.GatewayBot = loop.bot
            return get_response(request)
    
    return middleware