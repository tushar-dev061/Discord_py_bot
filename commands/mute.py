import discord
from discord.ext import commands

class AutoUnmute(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.guild_id = 728175523859005483  # The specific server ID
        self.mod_channel_id = 773863272222818354  # Set this to the ID of the mod channel where messages will be sent
        self.unmute_emoji = "✅"  # Emoji for mods to react to unmute
        

    @commands.Cog.listener()
    async def on_ready(self):
        
        guild = self.bot.get_guild(self.guild_id)
        if guild:
            # Find the mod channel by name or ID, set mod_channel_id if not set
            if not self.mod_channel_id:
                # Example: find channel named 'mod-channel'
                mod_channel = discord.utils.get(guild.text_channels, name='mod-channel')
                if mod_channel:
                    self.mod_channel_id = mod_channel.id
                    

    @commands.Cog.listener()
    async def on_message(self, message):
        
        # Ignore messages from bots
        if message.author.bot:
            return

        # Only handle DMs
        if isinstance(message.channel, discord.DMChannel):
            guild = self.bot.get_guild(self.guild_id)
            if not guild:
                
                return

            member = guild.get_member(message.author.id)
            if not member:
                
                return

            muted_role = discord.utils.get(guild.roles, name='Muted')
            if not muted_role:
                
                return

            if muted_role in member.roles:
                # Forward the message to the mod channel
                mod_channel = guild.get_channel(self.mod_channel_id)
                if not mod_channel:
                    
                    return

                embed = discord.Embed(
                    title=f"Muted user {member.display_name} ({member.id})",
                    description=message.content,
                    color=discord.Color.orange(),
                    timestamp=discord.utils.utcnow()
                )
                embed.set_footer(text="React with ✅ to unmute this user.")
                forwarded_message = await mod_channel.send(embed=embed)
                await forwarded_message.add_reaction(self.unmute_emoji)

                # Store the message ID and user ID mapping for reaction handling
                self.bot.forwarded_messages = getattr(self.bot, 'forwarded_messages', {})
                self.bot.forwarded_messages[forwarded_message.id] = member.id
                

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        
        # Ignore reactions by bots
        if user.bot:
            return

        message = reaction.message
        if not hasattr(self.bot, 'forwarded_messages'):
            
            return

        if message.id not in self.bot.forwarded_messages:
            
            return

        if str(reaction.emoji) != self.unmute_emoji:
            
            return

        guild = self.bot.get_guild(self.guild_id)
        if not guild:
            
            return

        member_id = self.bot.forwarded_messages[message.id]
        member = guild.get_member(member_id)
        if not member:
            
            return

        # Check if the user reacting has manage_roles permission
        member_reacting = guild.get_member(user.id)
        if not member_reacting:
            
            return
        if not member_reacting.guild_permissions.manage_roles:
            
            return

        muted_role = discord.utils.get(guild.roles, name='Muted')
        if muted_role and muted_role in member.roles:
            try:
                await member.remove_roles(muted_role, reason="Unmuted by moderator reaction")
                await message.channel.send(f"{member.mention} has been unmuted by {user.mention}.")
                try:
                    await member.send(f"You have been unmuted in {guild.name} by a moderator.")
                except:
                    pass
                # Remove the message from tracking
                del self.bot.forwarded_messages[message.id]
                
            except Exception as e:
                await message.channel.send(f"Failed to unmute {member.mention}. Error: {e}")
                

    @commands.command(name='autounmute_test')
    async def autounmute_test(self, ctx):
        await ctx.send("AutoUnmute Cog is active and responding.")

async def setup(bot):
    await bot.add_cog(AutoUnmute(bot))
