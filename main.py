import discord
from discord.ext import commands
import os
import asyncio
import B
from dotenv import load_dotenv

# Load .env file for token
load_dotenv()

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

client = commands.Bot(command_prefix='-', intents=intents, help_command=None)

# Start Flask server
B.b()

async def load_extensions():
    print("Starting to load command extensions...")
    for filename in os.listdir('./commands'):
        if filename.endswith('.py') and filename != '__init__.py':
            ext = f'commands.{filename[:-3]}'
            try:
                await client.load_extension(ext)
                print(f"Loaded: {ext}")
            except Exception as e:
                print(f"Failed to load {ext}: {e}")
    print("Finished loading command extensions.")

@client.event
async def on_ready():
    print(f'Logged in as {client.user} (ID: {client.user.id})')
    await client.change_presence(activity=discord.Activity(
        type=discord.ActivityType.watching, name="UNIQUE"))

@client.event
async def on_message(message: discord.Message):
    # Custom mention reply
    if (not message.author.bot and
        not message.mention_everyone and
        client.user in message.mentions):
        try:
            await message.channel.send(
                f"Hii {message.author.mention}! Use `-help` to get commands list."
            )
        except Exception as e:
            print(f"Failed to reply: {e}")

    await client.process_commands(message)

@client.command(name="reload")
@commands.is_owner()
async def reload_cmd(ctx, extension: str = None):
    if extension:
        try:
            await client.unload_extension(f"commands.{extension}")
            await client.load_extension(f"commands.{extension}")
            await ctx.send(f"Reloaded: {extension}")
        except Exception as e:
            await ctx.send(f"Failed to reload {extension}: {e}")
    else:
        for filename in os.listdir('./commands'):
            if filename.endswith('.py') and filename != '__init__.py':
                ext = f'commands.{filename[:-3]}'
                try:
                    await client.unload_extension(ext)
                    await client.load_extension(ext)
                except Exception as e:
                    await ctx.send(f"Failed: {ext} -> {e}")
        await ctx.send("Reload complete.")

@client.command(name="load")
@commands.is_owner()
async def load_cmd(ctx, extension: str):
    try:
        await client.load_extension(f"commands.{extension}")
        await ctx.send(f"Loaded: {extension}")
    except Exception as e:
        await ctx.send(f"Failed to load {extension}: {e}")

@client.command(name="help")
async def help_command(ctx):
    embed = discord.Embed(
        title="Help Menu",
        description="List of available commands",
        color=discord.Color.blue()
    )
    
    cogs = {}
    for command in client.commands:
        if not command.hidden:
            cog = command.cog_name or "General"
            cogs.setdefault(cog, []).append(command)

    for cog, cmds in cogs.items():
        cmd_list = "\n".join(f"-{cmd.name} → {cmd.help or 'No description'}" for cmd in cmds)
        embed.add_field(name=cog, value=cmd_list, inline=False)

    await ctx.send(embed=embed)

async def main():
    await load_extensions()
    token = os.getenv("TOKEN")
    if not token:
        print("❌ TOKEN missing in .env")
        return
    await client.start(token)

if __name__ == "__main__":
    asyncio.run(main())
