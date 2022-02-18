import discord
from yt_dlp import YoutubeDL
import requests
import os
from discord.ext import commands
from youtube_search import YoutubeSearch
from dotenv import load_dotenv
import random

load_dotenv()
client = commands.Bot(command_prefix='!')
FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}
song_queue = []

ytdl_format_options = {
    'format': 'worst',
    'extractaudio': True,
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
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


@client.event
async def on_ready():
    print('---------------------')
    print('BOT is now ONLINE')
    print('---------------------')


@client.command(brief='Bot makes a joke', description='The bot will randomly choose a Romanian joke.')
async def banc(ctx):
    joke_url = "https://romanian-jokes-api.herokuapp.com/v1/romanianjokes"
    jokes = requests.request("GET", joke_url).json()
    await ctx.send(jokes['joke'])


@client.command(brief='Bot makes a joke', description='The bot will randomly choose a Chuck Norris joke.')
async def joke(ctx):
    joke_url = "https://api.chucknorris.io/jokes/random"
    jokes = requests.request("GET", joke_url).json()
    await ctx.send(jokes['value'])


@client.command(brief='The bot will join the voice channel', description='The bot will join the voice channel you are summoning it from.')
async def join(ctx):
    if ctx.author.voice:
        channel = ctx.message.author.voice.channel
        await channel.connect()
    else:
        await ctx.send("Billy, Silly .. tiny Willy , you are not in a voice channel.")


@client.command(brief='The bot will leave the voice channel')
async def leave(ctx):
    if ctx.voice_client:
        await ctx.guild.voice_client.disconnect()
        await ctx.send("Bored of you guys, I left the voice channel")
    else:
        await ctx.send("Im a not in a voice channel")


@client.command(brief='Search on youtube', description='The bot will search on youtube for the first 10 query reponses')
async def search(ctx):
    song_name = ctx.message.content.replace('!search ', "")
    author = ctx.message.author
    list_songs = f"Searching :mag_right: {song_name}\n"
    results = YoutubeSearch(song_name, max_results=10).to_dict()
    for i in range(1, 11):
        if i != 10:
            list_songs += str(i) + ". " + results[i - 1].get('title') + '\n'
        else:
            list_songs += str(i) + ". " + results[i - 1].get('title')
    await ctx.message.channel.send(list_songs)
    try:
        msg = await client.wait_for('message', check=lambda message: (int(message.content) in range(1,11)) and message.author == author)
        await play(ctx, results[int(msg.content) - 1].get('title'))
    except ValueError:
        pass


@client.command(brief='Play a song by it\'s name', description='The bot will play the first song from the query, you can type the song name, youtube id, full URL')
async def play(ctx, song_name):
    voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
    if "!play " in ctx.message.content:
        song_name = ctx.message.content.replace('!play ', "")
    result = YoutubeSearch(song_name, max_results=1).to_dict()[0]
    song_queue.append(result)
    if voice.is_playing():
        await ctx.send(f'Song {result.get("title")} added to the queue')
    else:
        next_song(ctx, song_queue[0], voice)


def next_song(ctx, song_details, voice):
    with YoutubeDL(ytdl_format_options) as ydl:
        info = ydl.extract_info(f'https://youtu.be/{song_details.get("id")}', download=False)
        URL = info['formats'][0]['url']
        emb = discord.Embed(title=':notes: -Now playing- :notes:', description=song_details.get('title'), color=0x00fa11)
        emb.add_field(name='channel', value=song_details.get('channel'), inline=False)
        emb.add_field(name='duration', value=song_details.get('duration'), inline=False)
        emb.add_field(name='views', value=song_details.get('views'), inline=False)
        emb.add_field(name='published', value=song_details.get('publish_time'), inline=False)
        emb.add_field(name='link', value=f'https://youtu.be/{song_details.get("id")}', inline=False)
        client.loop.create_task(ctx.send(embed=emb))
        print(f'Playing: {song_details.get("title")}')
    del song_queue[0]
    voice.play(discord.FFmpegPCMAudio(URL, **FFMPEG_OPTIONS),after=lambda e: next_song(ctx, song_queue[0], voice) if (len(song_queue) > 0) else print('Finished playing all songs'))


@client.command(brief='Skip the current song', description='The bot will skip the current song as long as he has another following in the queue')
async def skip(ctx):
    voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
    if len(song_queue) > 0:
        await ctx.send("Skipping to the next song..")
        voice.stop()
    else:
        await ctx.send("There's no other song in the queue.")


@client.command(brief='Stop the current song', description='The bot will stop the current song.')
async def stop(ctx):
    voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
    voice.stop()


@client.command(brief='List the actual queue', description='Ask the bot to type the current state of the queue')
async def q(ctx):
    if len(song_queue) == 0:
        await ctx.send("There's no songs in the queue.")
    else:
        emb = discord.Embed(title=':palm_tree: -This is the actual queue- :palm_tree:', color=0x00fa11)
        for i in range(len(song_queue)):
            emb.add_field(name=f'{i+1}. {song_queue[i].get("title")}', value=song_queue[i].get("duration"), inline=False)
        await ctx.send(embed=emb)


@client.command(brief='Clear the actual queue', description='Ask the bot to clear the whole queue')
async def clear_q(ctx):
    song_queue.clear()
    await ctx.send("The queue has been cleared out.")


@client.command(brief='Pauses the audio',
                description='Bot will pause the audio in play, to resume it please see resume')
async def pause(ctx):
    voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
    if voice.is_playing():
        voice.pause()
    else:
        await ctx.send("Currently no audio is playing.")


@client.command(brief='Resumes the audio', description='Bot will resume the audio that has been previously paused')
async def resume(ctx):
    voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
    if voice.is_paused():
        voice.resume()
    else:
        await ctx.send("The audio is not paused.")


@client.event
async def on_command_error(ctx, error):
    await ctx.send(f"An error occured: {str(error)}")


@client.command(brief='Bot creates poll', description='Bot creates poll')
async def poll(ctx, *, message):
    emb = discord.Embed(title="Poll", description=f'{message}')
    msg = await ctx.channel.send(embed=emb)
    await msg.add_reaction('\N{THUMBS UP SIGN}')
    await msg.add_reaction('\N{THUMBS DOWN SIGN}')


@client.command(brief='Bot random picks', description='Bot random picks between the values you insert separated by space')
async def rnd(ctx):
    pick_from = ctx.message.content.replace('!random ', "")
    pick_from_list = pick_from.split(" ")
    await ctx.send(pick_from_list[random.randint(1, len(pick_from_list)) - 1])


client.run(os.environ['TOKEN'])
