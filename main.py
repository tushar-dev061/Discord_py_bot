import discord
from discord.ext import commands
import os
import asyncio
from dotenv import load_dotenv
import B  # your Flask keep-alive file

# ===================== ENV =====================
load_dotenv()

TOKEN = os.getenv("TOKEN")
if not TOKEN:
    raise RuntimeError("❌ TOKEN not found in environment variables")

# ===================== INTENTS =====================
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

# ===================== BOT =====================
bot = commands.Bot(
    command_prefix="-",
    intents=intents,
    help_command=None
)

# ===================== KEEP ALIVE =====================
B.b()

# ===================== EXTENSION LOADER =====================
async def load_extensions():
    print("📦 Loading command extensions...")
    for filename in os.listdir("./commands"):
        if filename.endswith(".py") and filename != "__init__.py":
            ext = f"commands.{filename[:-3]}"
            try:
                await bot.load_extension(ext)
                print(f"✅ Loaded: {ext}")
            except Exception as e:
                print(f"❌ Failed to load {ext}: {e}")
    print("🚀 All extensions loaded")

# ===================== EVENTS =====================
@bot.event
async def on_ready():
    print(f"🤖 Logged in as {bot.user} (ID: {bot.user.id})")
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name="UNIQUE"
        )
    )

@bot.event
async def on_message(message: discord.Message):
    if (
        not message.author.bot
        and bot.user in message.mentions
        and not message.mention_everyone
    ):
        try:
            await message.channel.send(
                f"Hi {message.author.mention}! Use `+help` to see commands."
            )
        except Exception as e:
            print("Reply failed:", e)

    await bot.process_commands(message)

# ===================== OWNER COMMANDS =====================
@bot.command()
@commands.is_owner()
async def reload(ctx, extension: str = None):
    if extension:
        try:
            await bot.unload_extension(f"commands.{extension}")
            await bot.load_extension(f"commands.{extension}")
            await ctx.send(f"♻ Reloaded `{extension}`")
        except Exception as e:
            await ctx.send(f"❌ {e}")
    else:
        for filename in os.listdir("./commands"):
            if filename.endswith(".py") and filename != "__init__.py":
                ext = f"commands.{filename[:-3]}"
                try:
                    await bot.unload_extension(ext)
                    await bot.load_extension(ext)
                except Exception as e:
                    await ctx.send(f"❌ {ext}: {e}")
        await ctx.send("✅ All extensions reloaded")

@bot.command()
@commands.is_owner()
async def load(ctx, extension: str):
    try:
        await bot.load_extension(f"commands.{extension}")
        await ctx.send(f"✅ Loaded `{extension}`")
    except Exception as e:
        await ctx.send(f"❌ {e}")

# ===================== HELP =====================
@bot.command(name="help")
async def help_command(ctx):
    embed = discord.Embed(
        title="Help Menu",
        description="Available Commands",
        color=discord.Color.blue()
    )

    cogs = {}
    for cmd in bot.commands:
        if not cmd.hidden:
            cog = cmd.cog_name or "General"
            cogs.setdefault(cog, []).append(cmd)

    for cog, cmds in cogs.items():
        embed.add_field(
            name=cog,
            value="\n".join(
                f"+{cmd.name} → {cmd.help or 'No description'}"
                for cmd in cmds
            ),
            inline=False
        )

    await ctx.send(embed=embed)

# ===================== MAIN =====================
async def main():
    await load_extensions()
    await bot.start(TOKEN)

if __name__ == "__main__":
    asyncio.run(main())

