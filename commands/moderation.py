from discord.ext import commands
import discord

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot



    @commands.command(name='ban', aliases=['b'])
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, member: discord.Member, *, reason=None):
        """Ban a member from the server."""
        try:
            await member.ban(reason=reason)
            await ctx.send(f'{member.mention} has been banned. Reason: {reason}')
            try:
                embed = discord.Embed(
                    title="You have been banned",
                    description=f"You have been banned from {ctx.guild.name}." + (f"\nReason: {reason}" if reason else ""),
                    color=discord.Color.red()
                )
                await member.send(embed=embed)
            except Exception as e:
                await ctx.send(f"Could not send DM to {member.mention}. They might have DMs disabled.")
        except Exception as e:
            await ctx.send(f'Failed to ban {member.mention}. Error: {e}')

    @commands.command(name='kick', aliases=['k'])
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, member: discord.Member, *, reason=None):
        """Kick a member from the server."""
        try:
            await member.kick(reason=reason)
            await ctx.send(f'{member.mention} has been kicked. Reason: {reason}')
            try:
                embed = discord.Embed(
                    title="You have been kicked",
                    description=f"You have been kicked from {ctx.guild.name}." + (f"\nReason: {reason}" if reason else ""),
                    color=discord.Color.orange()
                )
                await member.send(embed=embed)
            except Exception as e:
                await ctx.send(f"Could not send DM to {member.mention}. They might have DMs disabled.")
        except Exception as e:
            await ctx.send(f'Failed to kick {member.mention}. Error: {e}')

    @commands.command(name='purge', aliases=['clear', 'prune'])
    @commands.has_permissions(manage_messages=True)
    async def purge(self, ctx, amount: int):
        """Bulk delete messages in the channel."""
        try:
            deleted = await ctx.channel.purge(limit=amount)
            await ctx.send(f'Deleted {len(deleted)} messages.', delete_after=5)
        except Exception as e:
            await ctx.send(f'Failed to delete messages. Error: {e}')

    @commands.command(name='mute', aliases=['m'])
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
        try:
            print(f"Attempting to send DM to {member} after muting")
            embed = discord.Embed(
                title="You have been muted",
                description=(
                    f"You have been muted in {ctx.guild.name}.\n\n"
                    "Describe your reason for this conduct, your message will be sent to the moderators.\n"
                    "you will be unmuted as soon as we confirm your reason.\n"
                    "Please be patient and wait for a moderator to respond."
                ),
                color=discord.Color.red()
            )
            await member.send(embed=embed)
            print(f"DM sent to {member}")
        except Exception as e:
            print(f"Failed to send DM to {member}: {e}")
            await ctx.send(f"Could not send DM to {member.mention}. They might have DMs disabled.")


    @commands.command(name='unban', aliases=['ub'])
    @commands.has_permissions(ban_members=True)
    async def unban(self, ctx, user: discord.User, *, reason=None):
        """Unban a user from the server."""
        try:
            banned_users = [entry async for entry in ctx.guild.bans()]
            user_entry = next((entry for entry in banned_users if entry.user.id == user.id), None)
            if user_entry is None:
                await ctx.send(f'{user.mention} is not banned.')
                return
            await ctx.guild.unban(user, reason=reason)
            await ctx.send(f'{user.mention} has been unbanned. Reason: {reason}')
            try:
                embed = discord.Embed(
                    title="You have been unbanned",
                    description=f"You have been unbanned from {ctx.guild.name}." + (f"\nReason: {reason}" if reason else ""),
                    color=discord.Color.green()
                )
                await user.send(embed=embed)
            except Exception as e:
                await ctx.send(f"Could not send DM to {user.mention}. They might have DMs disabled.")
        except Exception as e:
            await ctx.send(f'Failed to unban {user.mention}. Error: {e}')

    @commands.command(name='unmute', aliases=['um'])
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
            try:
                embed = discord.Embed(
                    title="You have been unmuted",
                    description=f"You have been unmuted in {ctx.guild.name}.",
                    color=discord.Color.green()
                )
                await member.send(embed=embed)
            except Exception as e:
                await ctx.send(f"Could not send DM to {member.mention}. They might have DMs disabled.")
        except Exception as e:
            await ctx.send(f'Failed to unmute {member.mention}. Error: {e}')

    @commands.command(name='warn', aliases=['w'])
    @commands.has_permissions(manage_messages=True)
    async def warn(self, ctx, member: discord.Member, *, reason=None):
        """Warn a member in the server."""
        if not reason:
            await ctx.send('You must provide a reason for the warning.')
            return
        try:
            await ctx.send(f'{member.mention}, you have been warned. Reason: {reason}')
            try:
                embed = discord.Embed(
                    title="You have been warned",
                    description=f"You have been warned in {ctx.guild.name}. Reason: {reason}",
                    color=discord.Color.gold()
                )
                await member.send(embed=embed)
            except Exception as e:
                await ctx.send(f"Could not send DM to {member.mention}. They might have DMs disabled.")
            # Optionally, log the warning to a channel or file here
        except Exception as e:
            await ctx.send(f'Failed to warn {member.mention}. Error: {e}')

    @commands.command(name='slomo_enable', aliases=['sm_on'])
    @commands.has_permissions(manage_channels=True)
    async def slomo_enable(self, ctx, delay: int):
        """Enable slow mode in the channel with the specified delay in seconds."""
        try:
            await ctx.channel.edit(rate_limit_per_user=delay)
            await ctx.send(f'Slow mode enabled with a delay of {delay} seconds.')
        except Exception as e:
            await ctx.send(f'Failed to enable slow mode. Error: {e}')

    @commands.command(name='slomo_disable', aliases=['sm_off'])
    @commands.has_permissions(manage_channels=True)
    async def slomo_disable(self, ctx):
        """Disable slow mode in the channel."""
        try:
            await ctx.channel.edit(rate_limit_per_user=0)
            await ctx.send('Slow mode disabled.')
        except Exception as e:
            await ctx.send(f'Failed to disable slow mode. Error: {e}')


    @commands.command(name='lock')
    @commands.has_permissions(manage_channels=True)
    async def lock(self, ctx):
        """Lock the current channel by disabling send messages for everyone."""
        everyone_role = ctx.guild.default_role
        try:
            await ctx.channel.set_permissions(everyone_role, send_messages=False)
            await ctx.send(f"{ctx.channel.mention} has been locked.")
        except Exception as e:
            await ctx.send(f"Failed to lock the channel. Error: {e}")

    @commands.command(name='unlock')
    @commands.has_permissions(manage_channels=True)
    async def unlock(self, ctx):
        """Unlock the current channel by enabling send messages for everyone."""
        everyone_role = ctx.guild.default_role
        try:
            await ctx.channel.set_permissions(everyone_role, send_messages=True)
            await ctx.send(f"{ctx.channel.mention} has been unlocked.")
        except Exception as e:
            await ctx.send(f"Failed to unlock the channel. Error: {e}")

async def setup(bot):
    await bot.add_cog(Moderation(bot))
