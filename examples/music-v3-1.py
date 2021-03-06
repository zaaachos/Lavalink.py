#!/usr/bin/env python3

"""
This is an example code that shows how you would setup a simple music bot for Lavalink v2, v3 and v3.1.
This example is only compatible with the discord.py rewrite branch.
Because of the F-Strings, you also must have Python 3.6 or higher installed.
"""

import logging
import math
import re

import discord
from discord.ext import commands  # pylint: disable=ungrouped-imports

import lavalink

time_rx = re.compile('[0-9]+')

url_rx = re.compile('https?:\/\/(?:www\.)?.+')  # noqa: W605 pylint: disable=anomalous-backslash-in-string


class Music:
    def __init__(self, bot):
        self.bot = bot

        if not hasattr(bot, 'lavalink') or not bot.lavalink:
            lavalink.Client(bot=bot, loop=bot.loop, log_level=logging.DEBUG)

            bot.lavalink.nodes.add(lavalink.Regions.all(), password='youshallnotpass')
            self.bot.lavalink.register_hook(self._track_hook)

    def __unload(self):
        # Clear the players from Lavalink's internal cache
        self.bot.loop.create_task(self.bot.lavalink.players.safe_clear())
        self.bot.lavalink.unregister_hook(self._track_hook)
        self.bot.lavalink.destroy()
        self.bot.lavalink = None

    async def _track_hook(self, event):
        if not hasattr(event, 'player'):
            return
        channel = self.bot.get_channel(event.player.fetch('channel'))
        if not channel:
            return

        if isinstance(event, lavalink.Events.TrackStartEvent):
            await channel.send(embed=discord.Embed(title='Now playing:',
                                                   description=event.track.title,
                                                   color=discord.Color.blurple()))

        elif isinstance(event, lavalink.Events.QueueEndEvent):
            await channel.send('Queue ended! Why not queue more songs?')

    async def get_player(self, guild, create: bool = True):
        return await self.bot.lavalink.get_player(guild.id, create)

    @commands.command(name='play', aliases=['p'])
    @commands.guild_only()
    async def _play(self, ctx, *, query: str):
        """ Searches and plays a song from a given query. """
        player = await self.get_player(ctx.guild)

        query = query.strip('<>')

        if not url_rx.match(query):
            query = f'ytsearch:{query}'

        results = await self.bot.lavalink.get_tracks(query)

        if not results or (isinstance(results, dict) and not results['tracks']):
            return await ctx.send('Nothing found!')

        if isinstance(results, dict):
            tracks = results['tracks']
            if results['loadType'] == 'PLAYLIST_LOADED':
                await self.queue_playlist(player, tracks, ctx.channel, ctx.author, results['playlistInfo'])
            else:
                await self.queue_song(player, tracks, ctx.channel, ctx.author)
        else:
            if 'list' in query and 'ytsearch:' not in query:
                await self.queue_playlist(player, results, ctx.channel, ctx.author)
            else:
                await self.queue_song(player, results, ctx.channel, ctx.author)

        if not player.is_playing:
            await player.play()

    async def queue_song(self, player, tracks, channel, author):
        embed = discord.Embed(color=discord.Color.blurple())
        track = tracks[0]
        track_title = track["info"]["title"]
        track_uri = track["info"]["uri"]
        embed.title = "Track enqueued!"
        embed.description = f'[{track_title}]({track_uri})'
        await channel.send(embed=embed)
        player.add(requester=author.id, track=track)

    async def queue_playlist(self, player, tracks, channel, author, info: bool = False):
        embed = discord.Embed(color=discord.Color.blurple())
        for track in tracks:
            player.add(requester=author.id, track=track)

        embed.title = 'Playlist enqueued!'
        if info:
            embed.description = f'{info["name"]} - {len(tracks)} tracks'
        else:
            embed.description = f'Imported {len(tracks)} tracks from the playlist!'
        await channel.send(embed=embed)

    @commands.command(name='previous', aliases=['pv'])
    @commands.guild_only()
    async def _previous(self, ctx):
        """ Plays the previous song. """
        player = await self.get_player(ctx.guild)

        try:
            await player.play_previous()
        except lavalink.NoPreviousTrack:
            await ctx.send('There is no previous song to play.')

    @commands.command(name='playnow', aliases=['pn'])
    @commands.guild_only()
    async def _playnow(self, ctx, *, query: str):
        """ Plays immediately a song. """
        player = await self.get_player(ctx.guild)

        if not player.queue and not player.is_playing:
            return await ctx.invoke(self._play, query=query)

        query = query.strip('<>')

        if not url_rx.match(query):
            query = f'ytsearch:{query}'

        results = await self.bot.lavalink.get_tracks(query)

        if not results or (isinstance(results, dict) and not results['tracks']):
            return await ctx.send('Nothing found!')

        if isinstance(results, dict):
            track = results['tracks'].pop(0)
            if results['loadType'] == 'PLAYLIST_LOADED':
                await self.queue_playlist(player, results['tracks'], ctx.channel, ctx.author, results['playlistInfo'])
        else:
            track = results.pop(0)
            if 'list' in query and 'ytsearch:' not in query:
                await self.queue_playlist(player, results, ctx.channel, ctx.author)

        await player.play_now(requester=ctx.author.id, track=track)

    @commands.command(name='playat', aliases=['pa'])
    @commands.guild_only()
    async def _playat(self, ctx, index: int):
        """ Plays the queue from a specific point. Disregards tracks before the index. """
        player = await self.get_player(ctx.guild)

        if index < 1:
            return await ctx.send('Invalid specified index.')

        if len(player.queue) < index:
            return await ctx.send('This index exceeds the queue\'s length.')

        await player.play_at(index-1)

    @commands.command(name='seek')
    @commands.guild_only()
    async def _seek(self, ctx, *, time: str):
        """ Seeks to a given position in a track. """
        player = await self.get_player(ctx.guild)

        if not player.is_playing:
            return await ctx.send('Not playing.')

        seconds = time_rx.search(time)
        if not seconds:
            return await ctx.send('You need to specify the amount of seconds to skip!')

        seconds = int(seconds.group()) * 1000
        if time.startswith('-'):
            seconds *= -1

        track_time = player.position + seconds
        await player.seek(track_time)

        await ctx.send(f'Moved track to **{lavalink.Utils.format_time(track_time)}**')

    @commands.command(name='skip', aliases=['forceskip', 'fs'])
    @commands.guild_only()
    async def _skip(self, ctx):
        """ Skips the current track. """
        player = await self.get_player(ctx.guild)

        if not player.is_playing:
            return await ctx.send('Not playing.')

        await player.skip()
        await ctx.send('⏭ | Skipped.')

    @commands.command(name='stop')
    @commands.guild_only()
    async def _stop(self, ctx):
        """ Stops the player and clears its queue. """
        player = await self.get_player(ctx.guild)

        if not player.is_playing:
            return await ctx.send('Not playing.')

        player.queue.clear()
        await player.stop()
        await ctx.send('⏹ | Stopped.')

    @commands.command(name='now', aliases=['np', 'n', 'playing'])
    @commands.guild_only()
    async def _now(self, ctx):
        """ Shows some stats about the currently playing song. """
        player = await self.get_player(ctx.guild)
        song = 'Nothing'

        if player.current:
            position = lavalink.Utils.format_time(player.position)
            if player.current.stream:
                duration = '🔴 LIVE'
            else:
                duration = lavalink.Utils.format_time(player.current.duration)
            song = f'**[{player.current.title}]({player.current.uri})**\n({position}/{duration})'

        embed = discord.Embed(color=discord.Color.blurple(),
                              title='Now Playing', description=song)
        await ctx.send(embed=embed)

    @commands.command(name='queue', aliases=['q'])
    @commands.guild_only()
    async def _queue(self, ctx, page: int = 1):
        """ Shows the player's queue. """
        player = await self.get_player(ctx.guild)

        if not player.queue:
            return await ctx.send('There\'s nothing in the queue! Why not queue something?')

        items_per_page = 10
        pages = math.ceil(len(player.queue) / items_per_page)

        start = (page - 1) * items_per_page
        end = start + items_per_page

        queue_list = ''
        for index, track in enumerate(player.queue[start:end], start=start):
            queue_list += f'`{index + 1}.` [**{track.title}**]({track.uri})\n'

        embed = discord.Embed(colour=discord.Color.blurple(),
                              description=f'**{len(player.queue)} tracks**\n\n{queue_list}')
        embed.set_footer(text=f'Viewing page {page}/{pages}')
        await ctx.send(embed=embed)

    @commands.command(name='pause', aliases=['resume'])
    @commands.guild_only()
    async def _pause(self, ctx):
        """ Pauses/Resumes the current track. """
        player = await self.get_player(ctx.guild)

        if not player.is_playing:
            return await ctx.send('Not playing.')

        if player.paused:
            await player.set_pause(False)
            await ctx.send('⏯ | Resumed')
        else:
            await player.set_pause(True)
            await ctx.send('⏯ | Paused')

    @commands.command(name='volume', aliases=['vol'])
    @commands.guild_only()
    async def _volume(self, ctx, volume: int = None):
        """ Changes the player's volume. Must be between 0 and 1000. Error Handling for that is done by Lavalink. """
        player = await self.get_player(ctx.guild)

        if not volume:
            return await ctx.send(f'🔈 | {player.volume}%')

        await player.set_volume(volume)
        await ctx.send(f'🔈 | Set to {player.volume}%')

    @commands.command(name='bassboost', aliases=['bb'])
    async def _bassboost(self, ctx, level: str = None):
        """ Changes the player's bass frequencies up to 4 levels. OFF, LOW, MEDIUM, HIGH and INSANE. """
        player = await self.get_player(ctx.guild)

        levels = {
            'OFF': [(0, 0), (1, 0)],
            'LOW': [(0, 0.25), (1, 0.15)],
            'MEDIUM': [(0, 0.50), (1, 0.25)],
            'HIGH': [(0, 0.75), (1, 0.50)],
            'INSANE': [(0, 1), (1, 0.75)]
        }

        if not level:
            for k, v in levels.items():
                if [(0, player.equalizer[0]), (1, player.equalizer[1])] == v:
                    level = k
                    break
            return await ctx.send('Bass boost currently set on `{}`.'.format(level if level else 'CUSTOM'))

        gain = None

        for k in levels.keys():
            if k.startswith(level.upper()):
                gain = levels[k]
                break

        if not gain:
            return await ctx.send('Invalid level.')

        await player.set_gains(*gain)

        await ctx.send(f'Bass boost set on `{k}`.')

    @commands.command(name='shuffle')
    @commands.guild_only()
    async def _shuffle(self, ctx):
        """ Shuffles the player's queue. """
        player = await self.get_player(ctx.guild)
        if not player.is_playing:
            return await ctx.send('Nothing playing.')

        player.shuffle = not player.shuffle
        await ctx.send('🔀 | Shuffle ' + ('enabled' if player.shuffle else 'disabled'))

    @commands.command(name='repeat', aliases=['loop'])
    @commands.guild_only()
    async def _repeat(self, ctx):
        """ Repeats the current song until the command is invoked again. """
        player = await self.get_player(ctx.guild)

        if not player.is_playing:
            return await ctx.send('Nothing playing.')

        player.repeat = not player.repeat
        await ctx.send('🔁 | Repeat ' + ('enabled' if player.repeat else 'disabled'))

    @commands.command(name='remove')
    @commands.guild_only()
    async def _remove(self, ctx, index: int):
        """ Removes an item from the player's queue with the given index. """
        player = await self.get_player(ctx.guild)

        if not player.queue:
            return await ctx.send('Nothing queued.')

        if index > len(player.queue) or index < 1:
            return await ctx.send(f'Index has to be **between** 1 and {len(player.queue)}')

        index -= 1
        removed = player.queue.pop(index)

        await ctx.send(f'Removed **{removed.title}** from the queue.')

    @commands.command(name='find')
    @commands.guild_only()
    async def _find(self, ctx, *, query):
        """ Lists the first 10 search results from a given query. """
        if not query.startswith('ytsearch:') and not query.startswith('scsearch:'):
            query = 'ytsearch:' + query

        results = await self.bot.lavalink.get_tracks(query)

        if not results or not results['tracks']:
            return await ctx.send('Nothing found')

        tracks = results['tracks'][:10]  # First 10 results

        o = ''
        for index, track in enumerate(tracks, start=1):
            track_title = track["info"]["title"]
            track_uri = track["info"]["uri"]

            o += f'`{index}.` [{track_title}]({track_uri})\n'

        embed = discord.Embed(color=discord.Color.blurple(), description=o)
        await ctx.send(embed=embed)

    @commands.command(name='disconnect', aliases=['dc'])
    @commands.guild_only()
    async def _disconnect(self, ctx):
        """ Disconnects the player from the voice channel and clears its queue. """
        player = await self.get_player(ctx.guild)

        if not player.is_connected:
            return await ctx.send('Not connected.')

        if not ctx.author.voice or (player.is_connected and ctx.author.voice.channel.id != int(player.channel_id)):
            return await ctx.send('You\'re not in my voicechannel!')

        player.queue.clear()
        await player.disconnect()
        await ctx.send('*⃣ | Disconnected.')

    @_playnow.before_invoke
    @_previous.before_invoke
    @_play.before_invoke
    async def ensure_voice(self, ctx):
        """ A few checks to make sure the bot can join a voice channel. """
        player = await self.get_player(ctx.guild)

        if not player.is_connected:
            if not ctx.author.voice or not ctx.author.voice.channel:
                await ctx.send('You aren\'t connected to any voice channel.')
                raise commands.CommandInvokeError(
                    'Author not connected to voice channel.')

            permissions = ctx.author.voice.channel.permissions_for(ctx.me)

            if not permissions.connect or not permissions.speak:
                await ctx.send('Missing permissions `CONNECT` and/or `SPEAK`.')
                raise commands.CommandInvokeError(
                    'Bot has no permissions CONNECT and/or SPEAK')

            player.store('channel', ctx.channel.id)
            await player.connect(ctx.author.voice.channel.id)
        else:
            if player.connected_channel.id != ctx.author.voice.channel.id:
                return await ctx.send('Join my voice channel!')


def setup(bot):
    bot.add_cog(Music(bot))
