import discord
from discord.ext import commands
import yt_dlp
import asyncio
import os
from discord.ui import Button, View

class PlayerControls(View):
    def __init__(self, cog, ctx):
        super().__init__(timeout=300)
        self.cog = cog
        self.ctx = ctx

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user != self.ctx.author:
            await interaction.response.send_message(
                "❌ You can't control this player.",
                ephemeral=True
            )
            return False
        return True

    @discord.ui.button(label="Pause", style=discord.ButtonStyle.secondary, emoji="⏸")
    async def pause(self, interaction: discord.Interaction, button: Button):
        vc = self.ctx.voice_client
        if vc and vc.is_playing():
            vc.pause()
            await interaction.response.send_message("⏸ Paused", ephemeral=True)

    @discord.ui.button(label="Resume", style=discord.ButtonStyle.success, emoji="▶")
    async def resume(self, interaction: discord.Interaction, button: Button):
        vc = self.ctx.voice_client
        if vc and vc.is_paused():
            vc.resume()
            await interaction.response.send_message("▶ Resumed", ephemeral=True)

    @discord.ui.button(label="Skip", style=discord.ButtonStyle.primary, emoji="⏭")
    async def skip(self, interaction: discord.Interaction, button: Button):
        vc = self.ctx.voice_client
        if vc and vc.is_playing():
            vc.stop()
            await interaction.response.send_message("⏭ Skipped", ephemeral=True)

    @discord.ui.button(label="Stop", style=discord.ButtonStyle.danger, emoji="⏹")
    async def stop(self, interaction: discord.Interaction, button: Button):
        guild_id = self.ctx.guild.id
        vc = self.ctx.voice_client
        if vc:
            self.cog.song_queues[guild_id] = []
            vc.stop()
            await interaction.response.send_message(
                "⏹ Stopped & cleared queue",
                ephemeral=True
            )

    @discord.ui.button(label="Vol +", style=discord.ButtonStyle.secondary, emoji="🔊")
    async def vol_up(self, interaction: discord.Interaction, button: Button):
        guild_id = self.ctx.guild.id
        self.cog.volumes.setdefault(guild_id, 0.5)
        self.cog.volumes[guild_id] = min(2.0, self.cog.volumes[guild_id] + 0.1)
        if self.ctx.voice_client.source:
            self.ctx.voice_client.source.volume = self.cog.volumes[guild_id]
        await interaction.response.send_message(
            f"🔊 Volume: {int(self.cog.volumes[guild_id] * 100)}%",
            ephemeral=True
        )

    @discord.ui.button(label="Vol −", style=discord.ButtonStyle.secondary, emoji="🔉")
    async def vol_down(self, interaction: discord.Interaction, button: Button):
        guild_id = self.ctx.guild.id
        self.cog.volumes.setdefault(guild_id, 0.5)
        self.cog.volumes[guild_id] = max(0.0, self.cog.volumes[guild_id] - 0.1)
        if self.ctx.voice_client.source:
            self.ctx.voice_client.source.volume = self.cog.volumes[guild_id]
        await interaction.response.send_message(
            f"🔉 Volume: {int(self.cog.volumes[guild_id] * 100)}%",
            ephemeral=True
        )

# ====================== MUSIC COG ======================

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.song_queues = {}
        self.volumes = {}

    class YTDLSource(discord.PCMVolumeTransformer):
        def __init__(self, source, *, data, volume=0.5):
            super().__init__(source, volume)
            self.data = data
            self.title = data.get("title")
            self.thumbnail = data.get("thumbnail")

        @classmethod
        async def create(cls, query, *, loop):
            ytdl = yt_dlp.YoutubeDL({
                "format": "bestaudio/best",
                "quiet": True,
                "no_warnings": True,
                "default_search": "auto",
                "noplaylist": True,
                "source_address": "0.0.0.0"
            })

            data = await loop.run_in_executor(
                None, lambda: ytdl.extract_info(query, download=False)
            )

            if "entries" in data:
                data = data["entries"][0]

            source = discord.FFmpegPCMAudio(
                data["url"],
                before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
                options="-vn"
            )

            return cls(source, data=data)

    @commands.command(name="play", aliases=["p"])
    async def play(self, ctx, *, query):
        guild_id = ctx.guild.id
        self.song_queues.setdefault(guild_id, [])

        if not ctx.voice_client:
            if not ctx.author.voice:
                return await ctx.send("❌ Join a voice channel first.")
            await ctx.author.voice.channel.connect()

        player = await self.YTDLSource.create(query, loop=self.bot.loop)
        self.song_queues[guild_id].append(player)

        embed = discord.Embed(
            title="Added to Queue",
            description=f"🎵 **{player.title}**",
            color=discord.Color.green()
        )

        await ctx.send(embed=embed, view=PlayerControls(self, ctx))

        if not ctx.voice_client.is_playing():
            await self.play_next(ctx)

    async def play_next(self, ctx):
        guild_id = ctx.guild.id
        if not self.song_queues[guild_id]:
            return

        player = self.song_queues[guild_id][0]

        def after_playing(error):
            self.song_queues[guild_id].pop(0)
            if self.song_queues[guild_id]:
                asyncio.run_coroutine_threadsafe(
                    self.play_next(ctx), self.bot.loop
                )

        ctx.voice_client.play(player, after=after_playing)

        embed = discord.Embed(
            title="Now Playing",
            description=f"▶️ **{player.title}**",
            color=discord.Color.blue()
        )
        if player.thumbnail:
            embed.set_thumbnail(url=player.thumbnail)

        await ctx.send(embed=embed, view=PlayerControls(self, ctx))

# ====================== SETUP ======================

async def setup(bot):
    await bot.add_cog(Music(bot))
