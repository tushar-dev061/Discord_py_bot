import discord
from discord.ext import commands
import csv
import os
import random
import asyncio
import logging

class Verification(commands.Cog):
    """Verification system cog."""

    def __init__(self, bot):
        self.bot = bot
        self.verification_file = "verification_channels.csv"
        self.otp_storage = {}  # user_id: (otp, timestamp)
        self.load_verification_settings()
        self.logger = logging.getLogger('Verification')
        if not self.logger.hasHandlers():
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.DEBUG)

    def load_verification_settings(self):
        self.verification_settings = {}  # guild_id: {channel_id, role_id}
        if os.path.exists(self.verification_file):
            with open(self.verification_file, mode='r', newline='') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    guild_id = int(row['guild_id'])
                    channel_id = int(row['channel_id'])
                    role_id = int(row['role_id']) if row['role_id'] else None
                    self.verification_settings[guild_id] = {
                        'channel_id': channel_id,
                        'role_id': role_id
                    }

    def save_verification_settings(self):
        with open(self.verification_file, mode='w', newline='') as file:
            fieldnames = ['guild_id', 'channel_id', 'role_id']
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            for guild_id, settings in self.verification_settings.items():
                writer.writerow({
                    'guild_id': guild_id,
                    'channel_id': settings['channel_id'],
                    'role_id': settings.get('role_id', '')
                })

    @commands.command(name="enable_verification", help="Enable verification in a specific channel. Usage: !enable_verification #channel")
    @commands.has_permissions(administrator=True)
    async def enable_verification(self, ctx, channel: discord.TextChannel):
        guild_id = ctx.guild.id
        self.verification_settings[guild_id] = self.verification_settings.get(guild_id, {})
        self.verification_settings[guild_id]['channel_id'] = channel.id
        # If role_id not set, default to None
        if 'role_id' not in self.verification_settings[guild_id]:
            self.verification_settings[guild_id]['role_id'] = None
        self.save_verification_settings()
        await ctx.send(f"Verification enabled in {channel.mention}.")

    @commands.command(name="set_verification_role", help="Set the role to assign after verification. Usage: !set_verification_role @role")
    @commands.has_permissions(administrator=True)
    async def set_verification_role(self, ctx, role: discord.Role):
        guild_id = ctx.guild.id
        if guild_id not in self.verification_settings:
            await ctx.send("Please enable verification channel first using !enable_verification.")
            return
        self.verification_settings[guild_id]['role_id'] = role.id
        self.save_verification_settings()
        await ctx.send(f"Verification role set to {role.name}.")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        guild_id = message.guild.id if message.guild else None
        if not guild_id or guild_id not in self.verification_settings:
            return

        settings = self.verification_settings[guild_id]
        verification_channel_id = settings.get('channel_id')
        if not verification_channel_id or message.channel.id != verification_channel_id:
            return

        # Check if user is already verified
        role_id = settings.get('role_id')
        role = None
        if role_id:
            role = message.guild.get_role(role_id)
        else:
            role = discord.utils.get(message.guild.roles, name="Verified")

        if role in message.author.roles:
            embed = discord.Embed(title="Verification Info", description=f"{message.author.mention}, you already have the '{role.name}' role.", color=0x00ff00)
            await message.channel.send(embed=embed)
            return  # Already verified

        if role is None:
            await message.channel.send("Verification role not found. Please contact an admin to set the verification role.")
            return

        content = message.content.strip()

        if content.lower() == "verify":
            # Generate OTP
            otp = f"{random.randint(0, 9999):04d}"
            timestamp = asyncio.get_event_loop().time()
            self.otp_storage[message.author.id] = (otp, timestamp)
            self.logger.debug(f"Generated OTP {otp} for user {message.author} ({message.author.id}) in guild {guild_id}")
            embed = discord.Embed(title="Verification OTP", description=f"Your verification OTP is: **{otp}** \n Please enter this code in {message.channel.mention} to verify.", color=0x00ff00)
            embed.set_footer(text=f"Bot BY Evilboy")
            try:
                await message.author.send(embed=embed)
                await message.channel.send(embed=embed)
            except discord.Forbidden:
                embed = discord.Embed(title="Verification Error", description=f"{message.author.mention}, I couldn't send you a DM. Please enable DMs and try again.", color=0xff0000)
                await message.channel.send(embed=embed)
                return
            
            await message.channel.send(f"{message.author.mention}, your OTP has been sent via DM and displayed here. Please enter the OTP here to verify.")
            return

        # Check if message is OTP
        if message.author.id in self.otp_storage:
            expected_otp, timestamp = self.otp_storage[message.author.id]
            current_time = asyncio.get_event_loop().time()
            self.logger.debug(f"User {message.author} ({message.author.id}) entered OTP {content}, expected OTP {expected_otp}")
            if current_time - timestamp > 30:
                del self.otp_storage[message.author.id]
                embed = discord.Embed(title="Verification Error", description=f"{message.author.mention}, your OTP has expired. Please type 'verify' to generate a new one.", color=0xff0000)
                await message.channel.send(embed=embed)
                return
            if content == expected_otp:
                try:
                    await message.author.add_roles(role)
                    embed = discord.Embed(title="Verification Success", description=f"Thank you {message.author.mention}, you have been verified and given the '{role.name}' role.", color=0x00ff00)
                    await message.channel.send(embed=embed)
                    del self.otp_storage[message.author.id]
                    self.logger.debug(f"User {message.author} ({message.author.id}) verified successfully and OTP cleared.")
                except discord.Forbidden:
                    embed = discord.Embed(title="Verification Error", description="I do not have permission to assign roles. Please contact an admin.", color=0xff0000)
                    await message.channel.send(embed=embed)
                except Exception as e:
                    embed = discord.Embed(title="Verification Error", description=f"An error occurred during verification: {e}", color=0xff0000)
                    await message.channel.send(embed=embed)
            else:
                embed = discord.Embed(title="Verification Error", description=f"{message.author.mention}, the OTP you entered is incorrect. Please try again.", color=0xff0000)
                await message.channel.send(embed=embed)
        else:
            # Ignore other messages
            return

async def setup(bot):
    await bot.add_cog(Verification(bot))
