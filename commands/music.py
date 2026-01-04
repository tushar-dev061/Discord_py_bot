
import discord
from discord.ext import commands
import yt_dlp as youtube_dl
import asyncio
import os
from discord.ui import Button, View

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.song_queues = {}
        self.loop_modes = {}
        self.mode_247 = {}
        self.volumes = {}
        self.basses = {}

        self.ytdl_format_options = {
            'format': 'bestaudio/best',
            'outtmpl': 'downloads/%(extractor)s-%(id)s-%(title)s.%(ext)s',
            'restrictfilenames': True,
            'noplaylist': True,
            'nocheckcertificate': True,
            'ignoreerrors': False,
            'logtostderr': False,
            'quiet': True,
            'no_warnings': True,
            'default_search': 'auto',
            'source_address': '0.0.0.0'
        }

        self.ffmpeg_options = {
            'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
            'options': '-vn',
            'executable': 'ffmpeg/ffmpeg.exe'
        }

        self.ytdl = youtube_dl.YoutubeDL(self.ytdl_format_options)
        os.makedirs('downloads', exist_ok=True)

    class YTDLSource(discord.PCMVolumeTransformer):
        def __init__(self, source, *, data, volume=0.5):
            super().__init__(source, volume)
            self.data = data
            self.title = data.get('title')
            self.url = data.get('url')
            self.thumbnail = data.get('thumbnail')

        @classmethod
        async def from_url(cls, url, *, loop=None, stream=False):
            ytdl = youtube_dl.YoutubeDL({
                'format': 'bestaudio/best',
                'outtmpl': 'downloads/%(extractor)s-%(id)s-%(title)s.%(ext)s',
                'restrictfilenames': True,
                'noplaylist': True,
                'nocheckcertificate': True,
                'ignoreerrors': False,
                'logtostderr': False,
                'quiet': True,
                'no_warnings': True,
                'default_search': 'auto',
                'source_address': '0.0.0.0'
            })
            loop = loop or asyncio.get_event_loop()
            data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

            if 'entries' in data:
                data = data['entries'][0]

            filename = data['url'] if stream else ytdl.prepare_filename(data)
            return cls(discord.FFmpegPCMAudio(filename, **{
                'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
                'options': '-vn',
                'executable': 'ffmpeg/ffmpeg.exe'
            }), data=data)

    @commands.command(name='play', aliases=['p'], help='To play song')
    async def play(self, ctx, *, url):
        guild_id = ctx.guild.id
        if guild_id not in self.song_queues:
            self.song_queues[guild_id] = []
        if guild_id not in self.loop_modes:
            self.loop_modes[guild_id] = 'none'

        if not ctx.voice_client:
            if ctx.author.voice:
                channel = ctx.author.voice.channel
                await channel.connect()
            else:
                await ctx.send("You are not connected to a voice channel.")
                return

        async with ctx.typing():
            try:
                player = await self.YTDLSource.from_url(url, loop=self.bot.loop, stream=True)
                self.song_queues[guild_id].append(player)

                button_previous = Button(label="Previous", style=discord.ButtonStyle.secondary, emoji="⏮️")
                button_pause = Button(label="Pause", style=discord.ButtonStyle.secondary, emoji="⏸️")
                button_resume = Button(label="Resume", style=discord.ButtonStyle.success, emoji="▶️")
                button_stop = Button(label="Stop", style=discord.ButtonStyle.danger, emoji="⏹️")
                button_skip = Button(label="Skip", style=discord.ButtonStyle.primary, emoji="⏭️")
                button_vol_up = Button(label="Vol+", style=discord.ButtonStyle.secondary, emoji="🔊")
                button_vol_down = Button(label="Vol-", style=discord.ButtonStyle.secondary, emoji="🔉")
                button_bass_up = Button(label="Bass+", style=discord.ButtonStyle.secondary, emoji="🎛️")
                button_bass_down = Button(label="Bass-", style=discord.ButtonStyle.secondary, emoji="🎚️")

                async def previous_callback(interaction):
                    if interaction.user != ctx.author:
                        embed = discord.Embed(description="You can't control this playback.", color=discord.Color.red())
                        await interaction.response.send_message(embed=embed, ephemeral=True)
                        return
                    guild_id = ctx.guild.id
                    if guild_id in self.song_queues and len(self.song_queues[guild_id]) > 1:
                        # Move current song to end and play previous
                        current = self.song_queues[guild_id].pop(0)
                        self.song_queues[guild_id].insert(0, self.song_queues[guild_id].pop())
                        self.song_queues[guild_id].insert(0, current)
                        ctx.voice_client.stop()
                        embed = discord.Embed(description="Playing previous song.", color=discord.Color.blue())
                        await interaction.response.send_message(embed=embed, ephemeral=True)
                    else:
                        embed = discord.Embed(description="No previous song in queue.", color=discord.Color.red())
                        await interaction.response.send_message(embed=embed, ephemeral=True)

                async def pause_callback(interaction):
                    if interaction.user != ctx.author:
                        embed = discord.Embed(description="You can't control this playback.", color=discord.Color.red())
                        await interaction.response.send_message(embed=embed, ephemeral=True)
                        return
                    if ctx.voice_client and ctx.voice_client.is_playing():
                        ctx.voice_client.pause()
                        embed = discord.Embed(description="Paused the song.", color=discord.Color.orange())
                        await interaction.response.send_message(embed=embed, ephemeral=True)
                    else:
                        embed = discord.Embed(description="No song is playing.", color=discord.Color.red())
                        await interaction.response.send_message(embed=embed, ephemeral=True)

                async def resume_callback(interaction):
                    if interaction.user != ctx.author:
                        embed = discord.Embed(description="You can't control this playback.", color=discord.Color.red())
                        await interaction.response.send_message(embed=embed, ephemeral=True)
                        return
                    if ctx.voice_client and ctx.voice_client.is_paused():
                        ctx.voice_client.resume()
                        embed = discord.Embed(description="Resumed the song.", color=discord.Color.green())
                        await interaction.response.send_message(embed=embed, ephemeral=True)
                    else:
                        embed = discord.Embed(description="Song is not paused.", color=discord.Color.red())
                        await interaction.response.send_message(embed=embed, ephemeral=True)

                async def stop_callback(interaction):
                    if interaction.user != ctx.author:
                        embed = discord.Embed(description="You can't control this playback.", color=discord.Color.red())
                        await interaction.response.send_message(embed=embed, ephemeral=True)
                        return
                    if ctx.voice_client:
                        ctx.voice_client.stop()
                        guild_id = ctx.guild.id
                        if guild_id in self.song_queues:
                            self.song_queues[guild_id].clear()
                        embed = discord.Embed(description="Stopped and cleared the queue.", color=discord.Color.red())
                        await interaction.response.send_message(embed=embed, ephemeral=True)
                    else:
                        embed = discord.Embed(description="No audio is playing.", color=discord.Color.red())
                        await interaction.response.send_message(embed=embed, ephemeral=True)

                async def skip_callback(interaction):
                    if interaction.user != ctx.author:
                        embed = discord.Embed(description="You can't control this playback.", color=discord.Color.red())
                        await interaction.response.send_message(embed=embed, ephemeral=True)
                        return
                    if ctx.voice_client and ctx.voice_client.is_playing():
                        ctx.voice_client.stop()
                        embed = discord.Embed(description="Skipped the current song.", color=discord.Color.blue())
                        await interaction.response.send_message(embed=embed, ephemeral=True)
                    else:
                        embed = discord.Embed(description="No song is playing.", color=discord.Color.red())
                        await interaction.response.send_message(embed=embed, ephemeral=True)

                async def vol_up_callback(interaction):
                    if interaction.user != ctx.author:
                        embed = discord.Embed(description="You can't control this playback.", color=discord.Color.red())
                        await interaction.response.send_message(embed=embed, ephemeral=True)
                        return
                    guild_id = ctx.guild.id
                    if guild_id not in self.volumes:
                        self.volumes[guild_id] = 0.5
                    self.volumes[guild_id] = min(2.0, self.volumes[guild_id] + 0.1)
                    if ctx.voice_client and ctx.voice_client.source:
                        ctx.voice_client.source.volume = self.volumes[guild_id]
                    embed = discord.Embed(description=f"Volume increased to {int(self.volumes[guild_id] * 100)}%.", color=discord.Color.green())
                    await interaction.response.send_message(embed=embed, ephemeral=True)

                async def vol_down_callback(interaction):
                    if interaction.user != ctx.author:
                        embed = discord.Embed(description="You can't control this playback.", color=discord.Color.red())
                        await interaction.response.send_message(embed=embed, ephemeral=True)
                        return
                    guild_id = ctx.guild.id
                    if guild_id not in self.volumes:
                        self.volumes[guild_id] = 0.5
                    self.volumes[guild_id] = max(0.0, self.volumes[guild_id] - 0.1)
                    if ctx.voice_client and ctx.voice_client.source:
                        ctx.voice_client.source.volume = self.volumes[guild_id]
                    embed = discord.Embed(description=f"Volume decreased to {int(self.volumes[guild_id] * 100)}%.", color=discord.Color.green())
                    await interaction.response.send_message(embed=embed, ephemeral=True)

                async def bass_up_callback(interaction):
                    if interaction.user != ctx.author:
                        embed = discord.Embed(description="You can't control this playback.", color=discord.Color.red())
                        await interaction.response.send_message(embed=embed, ephemeral=True)
                        return
                    guild_id = ctx.guild.id
                    if guild_id not in self.basses:
                        self.basses[guild_id] = 0.0
                    self.basses[guild_id] = min(10.0, self.basses[guild_id] + 1.0)
                    embed = discord.Embed(description=f"Bass increased to {self.basses[guild_id]} dB.", color=discord.Color.green())
                    await interaction.response.send_message(embed=embed, ephemeral=True)

                async def bass_down_callback(interaction):
                    if interaction.user != ctx.author:
                        embed = discord.Embed(description="You can't control this playback.", color=discord.Color.red())
                        await interaction.response.send_message(embed=embed, ephemeral=True)
                        return
                    guild_id = ctx.guild.id
                    if guild_id not in self.basses:
                        self.basses[guild_id] = 0.0
                    self.basses[guild_id] = max(-10.0, self.basses[guild_id] - 1.0)
                    embed = discord.Embed(description=f"Bass decreased to {self.basses[guild_id]} dB.", color=discord.Color.green())
                    await interaction.response.send_message(embed=embed, ephemeral=True)

                async def queue_callback(interaction):
                    if interaction.user != ctx.author:
                        embed = discord.Embed(description="You can't control this playback.", color=discord.Color.red())
                        await interaction.response.send_message(embed=embed, ephemeral=True)
                        return
                    guild_id = ctx.guild.id
                    if guild_id not in self.song_queues or len(self.song_queues[guild_id]) == 0:
                        embed = discord.Embed(description="The queue is currently empty.", color=discord.Color.red())
                        await interaction.response.send_message(embed=embed, ephemeral=True)
                        return

                    queue_list = self.song_queues[guild_id]
                    queue_text = "\n".join(f"{i}. {player.title}" for i, player in enumerate(queue_list, start=1))
                    embed = discord.Embed(
                        title="Current Song Queue",
                        description=queue_text,
                        color=discord.Color.blue()
                    )
                    await interaction.response.send_message(embed=embed, ephemeral=True)

                button_previous.callback = previous_callback
                button_pause.callback = pause_callback
                button_resume.callback = resume_callback
                button_stop.callback = stop_callback
                button_skip.callback = skip_callback
                button_vol_up.callback = vol_up_callback
                button_vol_down.callback = vol_down_callback
                button_bass_up.callback = bass_up_callback
                button_bass_down.callback = bass_down_callback
                

                view = View()
                view.add_item(button_previous)
                view.add_item(button_pause)
                view.add_item(button_resume)
                view.add_item(button_stop)
                view.add_item(button_skip)
                view.add_item(button_vol_up)
                view.add_item(button_vol_down)
                view.add_item(button_bass_up)
                view.add_item(button_bass_down)
                

                embed = discord.Embed(
                    title="Added to Queue",
                    description=f"**{player.title}**",
                    color=discord.Color.green()
                )
                await ctx.send(embed=embed, view=view)

                if not ctx.voice_client.is_playing():
                    await self.play_next(ctx)
            except Exception as e:
                embed = discord.Embed(
                    title="Error",
                    description=f"An error occurred while trying to play the audio: {e}",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
                print(f"Error in play command: {e}")
                return

    async def play_next(self, ctx):
        guild_id = ctx.guild.id
        if guild_id not in self.song_queues or len(self.song_queues[guild_id]) == 0:
            embed = discord.Embed(description="Queue is empty.", color=discord.Color.red())
            await ctx.send(embed=embed)
            return

        loop_mode = self.loop_modes.get(guild_id, 'none')
        current_player = self.song_queues[guild_id][0]

        def after_playing(error):
            if error:
                print(f'Player error: {error}')
            else:
                print('Playback finished without error.')

            coro = None
            if loop_mode == 'song':
                coro = ctx.voice_client.play(current_player, after=after_playing)
            elif loop_mode == 'queue':
                self.song_queues[guild_id].append(self.song_queues[guild_id].pop(0))
                if len(self.song_queues[guild_id]) > 0:
                    next_player = self.song_queues[guild_id][0]
                    coro = ctx.voice_client.play(next_player, after=after_playing)
            else:
                self.song_queues[guild_id].pop(0)
                if len(self.song_queues[guild_id]) > 0:
                    next_player = self.song_queues[guild_id][0]
                    coro = ctx.voice_client.play(next_player, after=after_playing)

            if coro:
                fut = asyncio.run_coroutine_threadsafe(coro, self.bot.loop)
                try:
                    fut.result()
                except Exception as e:
                    print(f"Error in after_playing coroutine: {e}")

        ctx.voice_client.play(current_player, after=after_playing)
        embed = discord.Embed(
            title="Now Playing",
            description=f"**{current_player.title}**",
            color=discord.Color.blue()
        )
        if current_player.thumbnail:
            embed.set_thumbnail(url=current_player.thumbnail)
        await ctx.send(embed=embed)

    @commands.command(name='pause', aliases=['pa'], help='Pause the song')
    async def pause(self, ctx):
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.pause()
            embed = discord.Embed(description="Paused the song.", color=discord.Color.orange())
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(description="No audio is playing.", color=discord.Color.red())
            await ctx.send(embed=embed)

    @commands.command(name='resume', aliases=['r'], help='Resume the song')
    async def resume(self, ctx):
        if ctx.voice_client and ctx.voice_client.is_paused():
            ctx.voice_client.resume()
            embed = discord.Embed(description="Resumed the song.", color=discord.Color.green())
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(description="Audio is not paused.", color=discord.Color.red())
            await ctx.send(embed=embed)

    @commands.command(name='stop', aliases=['s'], help='Stop the song')
    async def stop(self, ctx):
        guild_id = ctx.guild.id
        if ctx.voice_client:
            ctx.voice_client.stop()
            if guild_id in self.song_queues:
                self.song_queues[guild_id].clear()
            embed = discord.Embed(description="Stopped and cleared the queue.", color=discord.Color.red())
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(description="No audio is playing.", color=discord.Color.red())
            await ctx.send(embed=embed)

    @commands.command(name='queue', aliases=['q'], help='Show the current song queue')
    async def show_queue(self, ctx):
        guild_id = ctx.guild.id
        if guild_id not in self.song_queues or len(self.song_queues[guild_id]) == 0:
            embed = discord.Embed(description="The queue is currently empty.", color=discord.Color.red())
            await ctx.send(embed=embed)
            return

        queue_list = self.song_queues[guild_id]
        queue_text = "\n".join(f"{i}. {player.title}" for i, player in enumerate(queue_list, start=1))
        embed = discord.Embed(
            title="Current Song Queue",
            description=queue_text,
            color=discord.Color.blue()
        )
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Music(bot))

