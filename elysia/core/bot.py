import asyncio
import datetime
import hikari
import lightbulb
import logging
import lolpython
import miru
import os
import pyfiglet
import zoneinfo

from .http import HTTPDaemon
from .conf import Config
from .log import logging
from ..lib.utils import utcnow
from ..lib.injection import load_injection_for_commands
from ..lib.permissions import Node, AccessIsDenied
from ..lib.hooks import require_not_denied
from ..daemons import run_daemons
from ..mvc.discord.hooks import DiscordEventHandler


class Bot(hikari.GatewayBot):
    def __init__(self, conf):
        self.conf: Config = conf
        super().__init__(conf.token, intents=hikari.Intents.ALL, logs=None)

        # Bot attributes
        self.logger: logging.Logger = logging.getLogger(conf.name)
        self.is_ready: asyncio.Event = asyncio.Event()
        self.last_instantiation: datetime.datetime = self.localnow()
        self.last_connection: datetime.datetime | None = None
        self.version: str = f"{self.conf.version} '{self.conf.version_tag}'"
        self._permissions_root: Node | None = None

        # Handle lightbulb
        self.lightbulb: lightbulb.Client = lightbulb.client_from_app(self, hooks=[require_not_denied])
        self.lightbulb.error_handler(self._on_exc_pipeline_error)
        
        # Handle miru
        self.miru: miru.Client = miru.Client(self)

        # Handle HTTP Daemon
        self._http_daemon: HTTPDaemon | None = None

        # Define events
        self.subscribe(hikari.StartingEvent, self._load_command_handler)
        self.subscribe(hikari.ShardReadyEvent, self._on_ready)

        # These events allow the MVC to handle Discord objects.
        self.subscribe(hikari.GuildEvent, DiscordEventHandler.handle_guild_event)
        self.subscribe(hikari.MemberEvent, DiscordEventHandler.handle_member_event)
        self.subscribe(hikari.ChannelEvent, DiscordEventHandler.handle_channel_event)
        self.subscribe(hikari.RoleEvent, DiscordEventHandler.handle_role_event)

    async def _load_command_handler(self, _) -> None:
        """Load Lightbulb."""
        await self.lightbulb.load_extensions("elysia.ext")

        await self.lightbulb.start()
        load_injection_for_commands(self.lightbulb)
    
    async def _on_exc_pipeline_error(self, exc: lightbulb.exceptions.ExecutionPipelineFailedException) -> bool:
        """
        Callback for execution pipeline errors.
        
        These occur when execution of a command fails for whatever reason.
        """
        if isinstance(exc.causes[0], AccessIsDenied):
            await exc.context.respond(exc.causes[0].message)
            return True
        return False
    
    @property
    def http_daemon(self) -> HTTPDaemon:
        if self._http_daemon is None:
            raise RuntimeError("Access to HTTP daemon made but it is not active.")
        return self._http_daemon

    async def _on_reinit(self) -> None:
        """
        Handle reinitialization condition.

        The bulk of the code in here only fires under the condition that
        Elysia has been reinitialized. If this is the case, the timestamp
        field in her operational variables will not be null. This is what
        allows her to know whether or not this is a *RE*initialization, and
        also what allows her to know how long it took, and what channel
        this information should be sent to.
        """
        pass
    
    async def _on_ready(self, _: hikari.ShardReadyEvent) -> None:
        """
        Handle ShardReadyEvent, completing initialization.

        Most of the stuff that happens here takes place immediately
        after forming a Discord API connection.
        """
        self.last_connection = self.localnow()
        self._permissions_root = Node.build_from_client(self.lightbulb)
        await DiscordEventHandler.run_model_update(self)
        self._http_daemon = await HTTPDaemon.run(self)

        self.is_ready.set()

        await self._on_reinit()
        
        self.logger.info("Starting internal daemons...")
        run_daemons(self)
        self.logger.info("Successfully completed boot.")
    
    def print_banner(self, *args, **kwargs):
        """Overload banner with Elysia's logo."""
        font = "univers"
        if font not in pyfiglet.Figlet().getFonts():
            os.system(f"python -m pyfiglet -L {os.path.join(self.conf.asset_dir, 'font/figlet/ANSI\\ Shadow.flf')}")
        f = pyfiglet.Figlet(font=font)
        lolpython.lol_py(f.renderText(self.conf.name))
        lolpython.lol_py(f"{self.conf.version} '{self.conf.version_tag}'")
        print("")
    
    @property
    def timezone(self) -> zoneinfo.ZoneInfo:
        """Timezone of Elysia herself."""
        return self.conf.timezone

    def localnow(self) -> datetime.datetime:
        """Shortcut to get Elysia's local time."""
        return utcnow().astimezone(self.timezone)

    @property
    def permissions_root(self) -> Node:
        """Elysia's root permissions node."""
        if self._permissions_root is None:
            raise RuntimeError("Permissions root has not been set yet.")
        return self._permissions_root
    
    async def close(self, ctx=None, kill=False) -> None:
        """
        Restart or kill Elysia.
        
        Args:
            ctx (lightbulb.Context): The context if this call is coming
                from a command.
            kill (bool): If True, Elysia will not restart afterwards.

        Elysia by default will restart herself when this is called. The
        external bash script checks for the presence of a file named "lock"
        in her root directory. If present, the bash script will exit the
        infinite loop it is in, resulting in a permanent shutdown.
        """
        if kill is True:
            with open(os.path.join(self.conf.root, "lock"), "w") as _:
                self.logger.info("Call to kill made, halting execution.")
        else:
            self.logger.info("Call to reinitialize made, halting execution.")

        await self.http_daemon.shutdown()
        self.logger.info(f"{self.conf.name} now shutting down.")
        await super().close()
