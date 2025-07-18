from discord.ext import commands
import discord

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='avatar')
    async def avatar(self, ctx, member: discord.Member = None):
        """Shows the avatar of the user or specified member."""
        member = member or ctx.author
        await ctx.send(f"{member.display_name}'s avatar: {member.avatar.url}")

    @commands.command(name='ban')
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, member: discord.Member, *, reason=None):
        """Ban a member from the server."""
        try:
            await member.ban(reason=reason)
            await ctx.send(f'{member.mention} has been banned. Reason: {reason}')
        except Exception as e:
            await ctx.send(f'Failed to ban {member.mention}. Error: {e}')

    @commands.command(name='kick')
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, member: discord.Member, *, reason=None):
        """Kick a member from the server."""
        try:
            await member.kick(reason=reason)
            await ctx.send(f'{member.mention} has been kicked. Reason: {reason}')
        except Exception as e:
            await ctx.send(f'Failed to kick {member.mention}. Error: {e}')

    @commands.command(name='purge')
    @commands.has_permissions(manage_messages=True)
    async def purge(self, ctx, amount: int):
        """Bulk delete messages in the channel."""
        try:
            deleted = await ctx.channel.purge(limit=amount)
            await ctx.send(f'Deleted {len(deleted)} messages.', delete_after=5)
        except Exception as e:
            await ctx.send(f'Failed to delete messages. Error: {e}')

    @commands.command(name='mute')
    @commands.has_permissions(manage_roles=True)
    async def mute(self, ctx, member: discord.Member, *, reason=None):
        """Mute a member in the server."""
        if not member:
            await ctx.send("You must specify a member to mute.")
            return
        guild = ctx.guild
        muted_role = discord.utils.get(guild.roles, name='Muted')

        if not muted_role:
            muted_role = await guild.create_role(name='Muted')

            for channel in guild.channels:
                await channel.set_permissions(muted_role, speak=False, send_messages=False, read_message_history=True, read_messages=False)

        await member.add_roles(muted_role, reason=reason)
        await ctx.send(f'{member.mention} has been muted.')


    @commands.command(name='ping', aliases=['p', 'latency'])
    async def ping(self, ctx):
        """Check the bot's latency."""
        latency = self.bot.latency * 1000  # Convert to milliseconds
        await ctx.send(f'Pong! Latency: {latency:.2f} ms')

    @commands.command(name='unban')
    @commands.has_permissions(ban_members=True)
    async def unban(self, ctx, user: discord.User, *, reason=None):
        """Unban a user from the server."""
        try:
            banned_users = await ctx.guild.bans()
            user_entry = next((entry for entry in banned_users if entry.user.id == user.id), None)
            if user_entry is None:
                await ctx.send(f'{user.mention} is not banned.')
                return
            await ctx.guild.unban(user, reason=reason)
            await ctx.send(f'{user.mention} has been unbanned. Reason: {reason}')
        except Exception as e:
            await ctx.send(f'Failed to unban {user.mention}. Error: {e}')

    @commands.command(name='unmute')
    @commands.has_permissions(manage_roles=True)
    async def unmute(self, ctx, member: discord.Member):
        """Unmute a member in the server."""
        guild = ctx.guild
        muted_role = discord.utils.get(guild.roles, name='Muted')
        if not muted_role:
            await ctx.send('Muted role does not exist.')
            return
        if muted_role not in member.roles:
            await ctx.send(f'{member.mention} is not muted.')
            return
        try:
            await member.remove_roles(muted_role)
            await ctx.send(f'{member.mention} has been unmuted.')
        except Exception as e:
            await ctx.send(f'Failed to unmute {member.mention}. Error: {e}')

    @commands.command(name='warn')
    @commands.has_permissions(manage_messages=True)
    async def warn(self, ctx, member: discord.Member, *, reason=None):
        """Warn a member in the server."""
        if not reason:
            await ctx.send('You must provide a reason for the warning.')
            return
        try:
            await ctx.send(f'{member.mention}, you have been warned. Reason: {reason}')
            # Optionally, log the warning to a channel or file here
        except Exception as e:
            await ctx.send(f'Failed to warn {member.mention}. Error: {e}')

    @commands.command(name='slomo_enable')
    @commands.has_permissions(manage_channels=True)
    async def slomo_enable(self, ctx, delay: int):
        """Enable slow mode in the channel with the specified delay in seconds."""
        try:
            await ctx.channel.edit(rate_limit_per_user=delay)
            await ctx.send(f'Slow mode enabled with a delay of {delay} seconds.')
        except Exception as e:
            await ctx.send(f'Failed to enable slow mode. Error: {e}')

    @commands.command(name='slomo_disable')
    @commands.has_permissions(manage_channels=True)
    async def slomo_disable(self, ctx):
        """Disable slow mode in the channel."""
        try:
            await ctx.channel.edit(rate_limit_per_user=0)
            await ctx.send('Slow mode disabled.')
        except Exception as e:
            await ctx.send(f'Failed to disable slow mode. Error: {e}')

async def setup(bot):
    await bot.add_cog(Moderation(bot))
