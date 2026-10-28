import dateutil
import lightbulb
import oronyx
import zoneinfo

from ...core.conf import Config
from ...mvc.discord.models import User
from ...mvc.advisor.models import Reminder, Task
from ...lib.utils import utcnow


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
        future = oronyx.get_future(user.localnow, self.time)
        if future is None:
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


@advise.command
class TaskCommand(
    lightbulb.SlashCommand,
    name="task",
    description=f"Create a task, allowing {conf.name} to remind you of said task."
):
    
    task = lightbulb.string("task", "What task should you be reminded of?")
    due_datetime = lightbulb.string("due_datetime", "The date and time on which the task is due. If no time is specified, it defaults to midnight.")
    notify_time = lightbulb.string("notify_before", "A time string saying how much time before the due date you should be reminded.")
    
    @lightbulb.invoke
    async def invoke(self, ctx: lightbulb.Context, user: User):
        if oronyx.get_future_obj(self.notify_time) is None:
            out = f"Invalid time string: `{self.notify_time}`."
            out += f"\nTo view examples of valid time strings, visit https://{conf.mvc.allowed_hosts[0]}/oronyx."
            return await ctx.respond(out)
        
        
        try:
            dt = dateutil.parser.parse(self.due_datetime)
        except dateutil.parser._parser.ParserError:
            return await ctx.respond(f"Could not understand the format of the datetime: `{self.due_datetime}`.")
        
        dt = dt.astimezone(zoneinfo.ZoneInfo(user.timezone))
        
        task = Task(
            name=self.task,
            notify=self.notify_time,
            utc_due_date=dt,
            assigned_to=user
        )
        
        await task.asave()
        await task.prefetch(ctx.client.app) # type: ignore

        await ctx.respond(f"A task was set. The reminder will occur `{self.notify_time}` at `{task.notify_after}`.")
    

        
        
        
