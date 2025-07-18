import discord
from discord.ext import commands
import os
import asyncio
import B

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

client = commands.Bot(command_prefix='--', intents=intents, help_command=None)
B.b()  # Start the Flask server in a separate thread
async def load_extensions():
    print("Starting to load command extensions...")
    for filename in os.listdir('./commands'):
        if filename.endswith('.py') and filename != '__init__.py':
            extension = f'commands.{filename[:-3]}'
            try:
                await client.load_extension(extension)
                print(f'Loaded extension {extension}')
            except Exception as e:
                print(f'Failed to load extension {extension}: {e}')
    print("Finished loading command extensions.")

@client.event
async def on_ready():
    print(f'Logged in as {client.user} (ID: {client.user.id})')
    print('------')
    await client.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="your server"))

    # Start copying messages continuously from source to target channel
    source_channel_id = 1302143373947174925
    target_channel_id = 1302143379387187233
    source_channel = client.get_channel(source_channel_id)
    target_channel = client.get_channel(target_channel_id)

    if source_channel is None or target_channel is None:
        print("Source or target channel not found.")
        return

    print("Copying service is active.")

@client.event
async def on_message(message):
    source_channel_id = 1360963446165995530
    target_channel_id = 1302143379387187233

    if message.channel.id == source_channel_id and not message.author.bot:
        target_channel = client.get_channel(target_channel_id)
        if target_channel is None:
            print("Target channel not found.")
            return

        content = f"{message.author.display_name}: {message.content}"
        files = []
        for attachment in message.attachments:
            fp = await attachment.to_file()
            files.append(fp)

        try:
            await target_channel.send(content, files=files)
        except Exception as e:
            print(f"Failed to copy message: {e}")

    await client.process_commands(message)

@client.command(name='reload')
@commands.is_owner()
async def reload(ctx, extension: str = None):
    """Reloads a command extension. Use without arguments to reload all."""
    if extension:
        try:
            await client.unload_extension(f'commands.{extension}')
            await client.load_extension(f'commands.{extension}')
            await ctx.send(f'Reloaded extension: {extension}')
        except Exception as e:
            await ctx.send(f'Failed to reload extension {extension}: {e}')
    else:
        reloaded = []
        failed = []
        for filename in os.listdir('./commands'):
            if filename.endswith('.py') and filename != '__init__.py':
                ext = f'commands.{filename[:-3]}'
                try:
                    await client.unload_extension(ext)
                    await client.load_extension(ext)
                    reloaded.append(ext)
                except Exception as e:
                    failed.append((ext, str(e)))
        msg = ''
        if reloaded:
            msg += f'Reloaded extensions: {", ".join(reloaded)}\n'
        if failed:
            msg += 'Failed to reload extensions:\n'
            for ext, err in failed:
                msg += f'{ext}: {err}\n'
        await ctx.send(msg or 'No extensions reloaded.')

@client.command(name='load')
@commands.is_owner()
async def load(ctx, extension: str):
    """Loads a command extension."""
    try:
        await client.load_extension(f'commands.{extension}')
        await ctx.send(f'Loaded extension: {extension}')
    except Exception as e:
        await ctx.send(f'Failed to load extension {extension}: {e}')

@client.command(name='help')
async def help_command(ctx):
    """Shows this message."""
    embed = discord.Embed(title="Help - List of Commands", color=discord.Color.blue())
    cogs = {}
    for command in client.commands:
        if not command.hidden:
            cog_name = command.cog_name or "No Category"
            if cog_name not in cogs:
                cogs[cog_name] = []
            cogs[cog_name].append(command)
    for cog_name, commands_list in cogs.items():
        sorted_commands = sorted(commands_list, key=lambda cmd: cmd.name)
        command_descriptions = "\n".join(f'!{cmd.name} - {cmd.help or "No description"}' for cmd in sorted_commands)
        embed.add_field(name=cog_name, value=command_descriptions, inline=False)
    await ctx.send(embed=embed)

async def main():
    await load_extensions()
    token = os.getenv('TOKEN')
    if not token:
        import sys
        if len(sys.argv) < 2:
            print("Please provide the client token as a command line argument or set the DISCORD_client_TOKEN environment variable.")
            return
        token = sys.argv[1]
    await client.start(token)

if __name__ == '__main__':
    asyncio.run(main())
