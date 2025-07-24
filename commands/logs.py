import discord
from discord.ext import commands
import csv
import os

LOGS_CSV = 'logs_config.csv'

def read_logs_config():
        config = {}
        if os.path.exists(LOGS_CSV):
            with open(LOGS_CSV, mode='r', newline='', encoding='utf-8') as f:
                reader = csv.reader(f)
                for row in reader:
                    if len(row) >= 3:
                        guild_id = int(row[0])
                        log_type = row[1]
                        channel_id = row[2]
                        if guild_id not in config:
                            config[guild_id] = {}
                        # For dump_channels, store as list of ints
                        if log_type == 'dump_channels':
                            if log_type not in config[guild_id]:
                                config[guild_id][log_type] = []
                            config[guild_id][log_type].append(int(channel_id))
                        else:
                            config[guild_id][log_type] = int(channel_id)
        return config

def write_logs_config(config):
    with open(LOGS_CSV, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        for guild_id, logs in config.items():
            for log_type, channel_id in logs.items():
                writer.writerow([guild_id, log_type, channel_id])

class Logs(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        print("Loading Logs cog and reading config...")
        self.config = read_logs_config()
        print(f"Loaded config: {self.config}")

    def save_config(self):
        print("Saving logs config...")
        write_logs_config(self.config)
        print("Logs config saved.")

    @commands.group(name='vlog', invoke_without_command=True)
    async def vlog(self, ctx):
        """Voice log commands group."""
        embed = discord.Embed(
            description="Use 'vlog en #channel' to enable or 'vlog di' to disable voice logs.",
            color=discord.Color.blue()
        )
        await ctx.send(embed=embed)

    @vlog.command(name='en')
    @commands.has_permissions(manage_channels=True)
    async def enable_voice_log(self, ctx, channel: discord.TextChannel):
        """Enable voice channel join logs in the specified channel."""
        guild_id = ctx.guild.id
        if guild_id not in self.config:
            self.config[guild_id] = {}
        self.config[guild_id]['voice'] = channel.id
        self.save_config()
        embed = discord.Embed(
            description=f"Voice logs enabled in {channel.mention}",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)

    @vlog.command(name='di')
    @commands.has_permissions(manage_channels=True)
    async def disable_voice_log(self, ctx):
        """Disable voice channel join logs."""
        guild_id = ctx.guild.id
        if guild_id in self.config and 'voice' in self.config[guild_id]:
            del self.config[guild_id]['voice']
            self.save_config()
            embed = discord.Embed(
                description="Voice logs disabled.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(
                description="Voice logs are not enabled.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if before.channel == after.channel:
            return  # No change in voice channel
        guild_id = member.guild.id
        if guild_id in self.config and 'voice' in self.config[guild_id]:
            channel_id = self.config[guild_id]['voice']
            log_channel = member.guild.get_channel(channel_id)
            if log_channel:
                if before.channel is None and after.channel is not None:
                    embed = discord.Embed(
                        title="Voice Channel Joined",
                        description=f"{member.display_name} joined voice channel {after.channel.name}.",
                        color=discord.Color.green()
                    )
                    embed.set_footer(text=f"Time: {discord.utils.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
                    await log_channel.send(embed=embed)
                elif before.channel is not None and after.channel is None:
                    embed = discord.Embed(
                        title="Voice Channel Left",
                        description=f"{member.display_name} left voice channel {before.channel.name}.",
                        color=discord.Color.red()
                    )
                    embed.set_footer(text=f"Time: {discord.utils.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
                    await log_channel.send(embed=embed)
                elif before.channel is not None and after.channel is not None:
                    embed = discord.Embed(
                        title="Voice Channel Moved",
                        description=f"{member.display_name} moved from voice channel {before.channel.name} to {after.channel.name}.",
                        color=discord.Color.orange()
                    )
                    embed.set_footer(text=f"Time: {discord.utils.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
                    await log_channel.send(embed=embed)

    # Additional commands and listeners for message deleted, message dump, member join/leave, invited by can be added similarly.

    @commands.group(name='mlog', invoke_without_command=True)
    async def mlog(self, ctx):
        """Message log commands group."""
        embed = discord.Embed(
            description="Use 'mlog en #channel' to enable or 'mlog di' to disable message delete logs.",
            color=discord.Color.blue()
        )
        embed.set_footer(text=f"Time: {discord.utils.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
        await ctx.send(embed=embed)

    @mlog.command(name='en')
    @commands.has_permissions(manage_channels=True)
    async def enable_message_log(self, ctx, channel: discord.TextChannel):
        """Enable message delete logs in the specified channel."""
        guild_id = ctx.guild.id
        if guild_id not in self.config:
            self.config[guild_id] = {}
        self.config[guild_id]['message_delete'] = channel.id
        self.save_config()
        embed = discord.Embed(
            description=f"Message delete logs enabled in {channel.mention}",
            color=discord.Color.green()
        )
        embed.set_footer(text=f"Time: {discord.utils.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
        await ctx.send(embed=embed)

    @mlog.command(name='di')
    @commands.has_permissions(manage_channels=True)
    async def disable_message_log(self, ctx):
        """Disable message delete logs."""
        guild_id = ctx.guild.id
        if guild_id in self.config and 'message_delete' in self.config[guild_id]:
            del self.config[guild_id]['message_delete']
            self.save_config()
            embed = discord.Embed(
                description="Message delete logs disabled.",
                color=discord.Color.red()
            )
            embed.set_footer(text=f"Time: {discord.utils.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(
                description="Message delete logs are not enabled.",
                color=discord.Color.red()
            )
            embed.set_footer(text=f"Time: {discord.utils.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
            await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        guild_id = message.guild.id if message.guild else None
        if guild_id and guild_id in self.config and 'message_delete' in self.config[guild_id]:
            channel_id = self.config[guild_id]['message_delete']
            log_channel = message.guild.get_channel(channel_id)
            if log_channel:
                author = message.author
                content = message.content or "[No content]"
                embed = discord.Embed(
                    title="Message Deleted",
                    color=discord.Color.red()
                )
                embed.set_footer(text=f"Time: {discord.utils.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
                embed.add_field(name="Channel", value=message.channel.mention, inline=True)
                embed.add_field(name="Author", value=author.display_name, inline=True)
                embed.add_field(name="Content", value=content, inline=False)
                await log_channel.send(embed=embed)

    @commands.command(name='backup')
    @commands.has_permissions(manage_messages=True)
    async def backup(self, ctx, number: int, target_channel: discord.TextChannel):
        """Backup recent messages from the current channel to the target channel."""
        try:
            source_channel = ctx.channel
            if not target_channel:
                await ctx.send("❌ Could not find the target channel.")
                return

            # Fetch the messages
            messages = await source_channel.history(limit=number).flatten()

            # Reverse to send in correct order
            messages.reverse()

            # Send the messages to the target channel
            for msg in messages:
                content = msg.content
                author = msg.author.display_name
                await target_channel.send(f"📨 **{author}**: {content}")

            await ctx.send(f"✅ Successfully backed up {len(messages)} messages to {target_channel.mention}")
        except Exception as e:
            await ctx.send(f"❌ An error occurred during backup: {e}")

    @commands.group(name='jlog', invoke_without_command=True)
    async def jlog(self, ctx):
        """Join/leave log commands group."""
        embed = discord.Embed(
            description="Use 'jlog en #channel' to enable or 'jlog di' to disable join/leave logs.",
            color=discord.Color.blue()
        )
        embed.set_footer(text=f"Time: {discord.utils.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
        await ctx.send(embed=embed)

    @jlog.command(name='en')
    @commands.has_permissions(manage_channels=True)
    async def enable_join_log(self, ctx, channel: discord.TextChannel):
        """Enable join/leave logs in the specified channel."""
        guild_id = ctx.guild.id
        if guild_id not in self.config:
            self.config[guild_id] = {}
        self.config[guild_id]['join_leave'] = channel.id
        self.save_config()
        embed = discord.Embed(
            description=f"Join/leave logs enabled in {channel.mention}",
            color=discord.Color.green()
        )
        embed.set_footer(text=f"Time: {discord.utils.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
        await ctx.send(embed=embed)

    @jlog.command(name='di')
    @commands.has_permissions(manage_channels=True)
    async def disable_join_log(self, ctx):
        """Disable join/leave logs."""
        guild_id = ctx.guild.id
        if guild_id in self.config and 'join_leave' in self.config[guild_id]:
            del self.config[guild_id]['join_leave']
            self.save_config()
            embed = discord.Embed(
                description="Join/leave logs disabled.",
                color=discord.Color.red()
            )
            embed.set_footer(text=f"Time: {discord.utils.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(
                description="Join/leave logs are not enabled.",
                color=discord.Color.red()
            )
            embed.set_footer(text=f"Time: {discord.utils.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
            await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        guild_id = member.guild.id
        if guild_id in self.config and 'join_leave' in self.config[guild_id]:
            channel_id = self.config[guild_id]['join_leave']
            log_channel = member.guild.get_channel(channel_id)
            if log_channel:
                embed = discord.Embed(
                    title="Member Joined",
                    description=f"{member.display_name} has joined the server.",
                    color=discord.Color.green()
                )
                embed.set_footer(text=f"Time: {discord.utils.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
                await log_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        guild_id = member.guild.id
        if guild_id in self.config and 'join_leave' in self.config[guild_id]:
            channel_id = self.config[guild_id]['join_leave']
            log_channel = member.guild.get_channel(channel_id)
            if log_channel:
                embed = discord.Embed(
                    title="Member Left",
                    description=f"{member.display_name} has left the server.",
                    color=discord.Color.red()
                )
                embed.set_footer(text=f"Time: {discord.utils.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
                await log_channel.send(embed=embed)

    @commands.group(name='ilog', invoke_without_command=True)
    async def ilog(self, ctx):
        """Invite log commands group."""
        embed = discord.Embed(
            description="Use 'ilog en #channel' to enable or 'ilog di' to disable invite logs.",
            color=discord.Color.blue()
        )
        embed.set_footer(text=f"Time: {discord.utils.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
        await ctx.send(embed=embed)

    @ilog.command(name='en')
    @commands.has_permissions(manage_channels=True)
    async def enable_invite_log(self, ctx, channel: discord.TextChannel):
        """Enable invite logs in the specified channel."""
        guild_id = ctx.guild.id
        if guild_id not in self.config:
            self.config[guild_id] = {}
        self.config[guild_id]['invite'] = channel.id
        self.save_config()
        embed = discord.Embed(
            description=f"Invite logs enabled in {channel.mention}",
            color=discord.Color.green()
        )
        embed.set_footer(text=f"Time: {discord.utils.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
        await ctx.send(embed=embed)

    @ilog.command(name='di')
    @commands.has_permissions(manage_channels=True)
    async def disable_invite_log(self, ctx):
        """Disable invite logs."""
        guild_id = ctx.guild.id
        if guild_id in self.config and 'invite' in self.config[guild_id]:
            del self.config[guild_id]['invite']
            self.save_config()
            embed = discord.Embed(
                description="Invite logs disabled.",
                color=discord.Color.red()
            )
            embed.set_footer(text=f"Time: {discord.utils.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(
                description="Invite logs are not enabled.",
                color=discord.Color.red()
            )
            embed.set_footer(text=f"Time: {discord.utils.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
            await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        guild_id = member.guild.id
        if guild_id in self.config and 'invite' in self.config[guild_id]:
            channel_id = self.config[guild_id]['invite']
            log_channel = member.guild.get_channel(channel_id)
            if log_channel:
                # Invite tracking requires cache of invites
                invites_before = await member.guild.invites()
                # This simplistic approach may not be accurate; advanced tracking requires more state management
                embed = discord.Embed(
                    title="Member Joined (Invite)",
                    description=f"{member.display_name} joined the server. (Invite tracking not fully implemented)",
                    color=discord.Color.green()
                )
                embed.set_footer(text=f"Time: {discord.utils.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
                await log_channel.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Logs(bot))
