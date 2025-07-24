from discord.ext import commands
import re
import discord

class UtilityCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='enlarge', help='Enlarge one or more custom or unicode emojis. Usage: !enlarge <emoji1> <emoji2> ...')
    async def enlarge_emoji(self, ctx, *emojis: str):
        """
        Takes one or more emoji strings and sends larger images or representations of the emojis.
        Supports custom emojis in the format <:name:id> or <a:name:id> and unicode emojis.
        """
        custom_emoji_pattern = r"<a?:\w+:(\d+)>"
        urls = []
        if not emojis:
            await ctx.send("Please provide at least one emoji to enlarge.")
            return
        for emoji in emojis:
            match = re.match(custom_emoji_pattern, emoji)
            if match:
                emoji_id = match.group(1)
                url = f"https://cdn.discordapp.com/emojis/{emoji_id}.png?size=128"
                urls.append(url)
            else:
                # Convert unicode emoji to twemoji image URL
                # Get codepoints of emoji characters
                codepoints = '-'.join(f"{ord(c):x}" for c in emoji)
                twemoji_url = f"https://twemoji.maxcdn.com/v/latest/72x72/{codepoints}.png"
                urls.append(twemoji_url)
        # Send all URLs in one message separated by newlines
        await ctx.send('\n'.join(urls))

    @commands.command(name='post', help='Send plain text to a specified channel. Usage: !post <#channel> <text>')
    @commands.has_permissions(manage_channels=True)
    async def post(self, ctx, channel: discord.TextChannel, *, text: str):
        """
        Sends plain text message to the specified channel.
        """
        await channel.send(text)
        await ctx.send(f"Message sent to {channel.mention}")

    @commands.command(name='post_embed', help='Send an embed with text to a specified channel. Usage: !post_embed <#channel> <text>')
    async def post_embed(self, ctx, channel: discord.TextChannel, *, text: str):
        """
        Sends an embed with the given text to the specified channel.
        """
        embed = discord.Embed(title=ctx.guild.name, description=text, color=discord.Color.blue())
        await channel.send(embed=embed)
        await ctx.send(f"Embed message sent to {channel.mention}")

async def setup(bot):
    await bot.add_cog(UtilityCommands(bot))
