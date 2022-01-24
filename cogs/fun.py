import discord
from discord.ext import commands
import requests
import random
from bs4 import BeautifulSoup
import json

class Fun(commands.Cog):

    config = {}
    with open('config/config.json','r') as f:
        config = json.load(f)

    keys = {}
    with open('config/keys.json','r') as f:
        keys = json.load(f)

    OWNER_ID = config["ownerId"]
    TOKEN = config["token"]

    def __init__(self, bot):
            self.bot = bot

    @commands.command()
    async def cat(self, ctx):
        await ctx.send(requests.get('https://api.thecatapi.com/v1/images/search').json()[0]['url'])

    @commands.command()
    async def shiba(self, ctx):
        await ctx.send(requests.get('http://shibe.online/api/shibes?count=1&true=false&httpsUrls=true').json()[0])

    @commands.command()
    async def bird(self, ctx):
        await ctx.send(requests.get('http://shibe.online/api/birds?count=1&true=false&httpsUrls=true').json()[0])

    @commands.command()
    async def egg(self, ctx):
        hits = requests.get('https://pixabay.com/api/?key='+self.keys['pixabay']+'&q=egg&per_page=200').json()['hits']
        await ctx.send(hits[random.randint(0,len(hits))]['webformatURL'])

    @commands.command(aliases=['im'])
    async def image(self, ctx, *, search):
        hits = requests.get('https://pixabay.com/api/?key='+self.keys['pixabay']+'&q={}&per_page=10'.format(search)).json()['hits']
        if len(hits) == 0:
            await ctx.send('no results')
            return
        await ctx.send(random.choice(hits)['webformatURL'])

    @commands.command()
    async def bort(self, ctx):
        await ctx.send('bort')
        await ctx.message.delete()

    async def get_quizzes(self):
        url = 'https://www.buzzfeed.com/quizzes'
        html = requests.get(url).text
        soup = BeautifulSoup(html, 'html.parser')
        output = []

        for feature in soup.find_all('div', 'featured-card__body'):
            output.append(feature.a.get('href'))

        for card in soup.find_all('article', 'story-card'):
            output.append(card.a.get('href'))

        return output

    @commands.command(aliases=['bz'])
    async def buzzfeed(self, ctx):
        res = await self.get_quizzes()
        await ctx.send(random.choice(res))

    @commands.command()
    async def nicki(self, ctx):
        await ctx.send('nicki minaj is the queen of rap')

    @commands.command(aliases=['echo'])
    async def say(self, ctx, *, mes):
        try:
            await ctx.message.delete()
        except Exception:
            pass
        await ctx.send(mes)


    async def get_emojis(self):
        emoji_storage_server_id = self.config['emojiServer']
        guild = await self.bot.fetch_guild(emoji_storage_server_id)
        emojis = guild.emojis
        return emojis

    @commands.command(aliases=['list_emoji'])
    async def list_emojis(self, ctx):
        MAX = 27
        emojis = await self.get_emojis()
        i = 0
        for i in range(len(emojis)//MAX):
            m = ' '.join(list(map(lambda e: str(e), emojis[MAX*i:MAX*(i+1)])))
            await ctx.send(m)
        
        m = ' '.join(list(map(lambda e: str(e), emojis[len(emojis)-(len(emojis) % 27):])))
        await ctx.send(m)

    @commands.command(description = 'provide an optional link to message to react to, defaults to most recent message')
    async def react(self, ctx, emoji_name, messagelink=None):
        
        emojis = await self.get_emojis()
        reaction = None
        found = False

        for e in emojis:
            if e.name == emoji_name:
                reaction = e
                found = True

        if not found:
            reaction = emoji_name

        message = None

        if messagelink == None:
            async for m in ctx.message.channel.history(limit = 2):
                message = m
        else:
            try:
                ids = messagelink.split('/')
                
                channelid = int(ids[5])
                messageid = int(ids[6])

                channel = await self.bot.fetch_channel(channelid)
                message = await channel.fetch_message(messageid)
                
            except ValueError:
                await ctx.send('invalid message link')
                return
                
        await message.add_reaction(reaction)
        await ctx.message.delete()

    @commands.command(description = 'set delete to \'y\' \'yes\' or \'delete\' to delete your message')
    async def emoji(self, ctx, *emoji_names):
        names = list(emoji_names)
        del_arg = names[-1]
        delete = False

        if del_arg in ['y', 'yes', 'delete']:
            del names[-1]
            delete = True

        msg = ''
        emojis = await self.get_emojis()

        for emoji_name in names:
            for e in emojis:
                if e.name == emoji_name:
                    msg += str(e) + '\n'
                    break
        
        if delete:
            await ctx.message.delete()
        
        if msg == '':
            await ctx.send('no emoji found')
        else:
            await ctx.send(msg)

    @commands.command()
    async def bestie(self, ctx):
        await ctx.send('my beautiful bestie it\'s time to wake up <:catwake:801244567167959111>')

    @commands.command()
    async def simp(self, ctx):
        with open('media/fun/pickups.txt', 'r') as f:
            pickups = f.read().split('\n')
            await ctx.send(random.choice(pickups)[6:-26])

    @commands.command(aliases=['sixth'])
    async def raccoon(self, ctx):
        await ctx.send('https://raw.githubusercontent.com/datitran/raccoon_dataset/master/images/raccoon-{}.jpg'.format(random.randint(1,200)))

    @commands.Cog.listener()
    async def on_message(self, m):
        if 'forgor' in m.content:
            await m.add_reaction('\U0001F480')

        # await self.bot.invoke(await self.bot.get_context(m))

def setup(bot):
    bot.add_cog(Fun(bot))