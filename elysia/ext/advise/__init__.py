import lightbulb
import oronyx

from ...core.conf import Config
from ...mvc.discord.models import User
from ...mvc.advisor.models import Reminder


conf = Config.load()
advise = lightbulb.Loader()


@advise.command
class ChoresCommand(
    lightbulb.SlashCommand,
    name="chores",
    description="See the current chores you must do."
):

    @lightbulb.invoke
    async def invoke(self, ctx: lightbulb.Context):
        await ctx.respond("PONG! 🏓")


@advise.command
class RemindCommand(
    lightbulb.SlashCommand,
    name="remind",
    description=f"Tell {conf.name} to remind you of something."
):
    
    time = lightbulb.string("future", "The rule by which you should be reminded.")
    text = lightbulb.string("about", "What you should be reminded of.")
    recurring = lightbulb.boolean("recurring", "Should this reminder recur?", default=False)
    
    @lightbulb.invoke
    async def invoke(self, ctx: lightbulb.Context, user: User):
        scheduler = oronyx.get_scheduler(self.time)
        if scheduler is None:
            out = f"Invalid time string: `{self.time}`."
            out += f"\nTo view examples of valid time strings, visit https://{conf.mvc.allowed_hosts[0]}/oronyx."
            return await ctx.respond(out)
        
        reminder = Reminder(
            user=user,
            rule=self.time,
            text=self.text
        )
        
        await reminder.asave()
        await reminder.prefetch()

        await ctx.respond(f"A reminder was set for `{reminder.rule}`. The next occurrence will be at `{reminder.future}`.")
        
    

        
        
        
