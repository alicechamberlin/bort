import discord
from discord.ext import commands
from urllib import request, parse
import requests
import json
import random

class Economy(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    async def post_coins(self, name, id, dcoins, dxp, level):
        params = {"name":name,"apiKey":"e9c36cf3828611d5975aa77f8d10871b","dcoins":dcoins,"dxp":dxp,"level":level}

        data = parse.urlencode(params).encode()
        url = 'http://jennythepython.pythonanywhere.com/playerCoins/'+str(id)
        req = request.Request(url, data = data, headers={'User-Agent' : "Magic Browser"}) 
        responseBytes = request.urlopen(req).read()
        responseObject = json.loads(responseBytes.decode('utf-8'))
        return (responseObject)

    async def check_coins(self, user_id):
        return (await self.get_coins(user_id))["message"] != "unknown player"

    async def get_coins(self, id):

        url = 'http://jennythepython.pythonanywhere.com/playerCoins/'+str(id)
        req = request.Request(url, headers={'User-Agent' : "Magic Browser"}) 
        responseBytes = request.urlopen(req).read()
        responseObject = json.loads(responseBytes.decode('utf-8'))
        return (responseObject)

    def next_exp(self, level):
        total = 0
        for i in range(level + 1):
            total += 100 * int(3 ** (i / 10))
        return total

    async def add_exp(self, user, channel, amount):
        exp = 0
        level = 0
        if await self.check_coins(user.id):
            exp = (await self.get_coins(user.id))["xp"]
            level = (await self.get_coins(user.id))["level"]
        exp += amount
        while exp > self.next_exp(level):
            level += 1
            congratsRequest = requests.get("https://api.giphy.com/v1/gifs/search?q=bunny&api_key=INJuIdbai3pyu6J4Kk0HFikfDanmbZMM&limit=100").json()["data"]
            congratsLinkObject = congratsRequest[int(random.random() * len(congratsRequest))]
            congratsLink = congratsLinkObject["images"]["fixed_height"]["url"]
            congratsLink = congratsLink.replace("\\/", "/")
            embed = discord.Embed(
                title = "Level Up!",
                description = "Congrats! You are now level `" + str(level) + "`!"
            )
            embed.set_thumbnail(url = congratsLink)
            embed.set_author(name = user.name, icon_url = user.avatar_url)

            await channel.send(embed = embed)
        await self.post_coins(user.name, user.id, 0, amount, level)

    async def add_coins(self, user, channel, amount):
        return await self.post_coins(user.name, user.id, amount, 0, (await self.get_coins(user.id))["level"])

    @commands.command(aliases=['ld','lb'])
    async def leaderboard(self, ctx):
        
        url = 'http://jennythepython.pythonanywhere.com/leaderboard'
        req = request.Request(url, headers={'User-Agent' : "Magic Browser"}) 
        responseBytes = request.urlopen(req).read()
        resOb = json.loads(responseBytes.decode('utf-8'))
        msg = ["Rank  Name              Level   Exp   Bitecoins   \n"]
        rank = 0       
        for dict in resOb["leaderboard"]:
            rank += 1
            msg.append(str(rank)+" "*(6-(len(str(rank))))+dict["name"]+" "*(18-len(dict["name"]))+str(dict["level"])+\
                " "*(8-len(str(dict["level"])))+str(dict["xp"])+" "*(9-len(str(dict["xp"])))+' '*(6-len(str(dict['coins'])))+str(dict['coins']))
        ld = "\n".join(msg)
        while len(ld) > 1992:
            await ctx.send('```\n'+'\n'.join(ld[:1992].split('\n')[:-1])+'\n```')
            ld = '\n'.join(ld.split('\n')[len(ld[:1992].split('\n')[:-1]):])
        await ctx.send('```\n'+ld+'\n```')

    @commands.command()
    async def stats(self, ctx, *, member : discord.Member = None):
        if not member:
            member = ctx.author
        msg = await self.get_coins(member.id)
        embed = discord.Embed(title = 'level '+str(msg['level']), description = 'cumulative xp: `'+str(msg['xp'])+'`', color = member.color)
        embed.add_field(name = 'xp to next level', value = '`'+str(self.next_exp(msg['level'])-msg['xp'])+'`')
        embed.add_field(name = 'bitecoins', value = '`'+str(msg['coins'])+'`')
        embed.set_author(name = member.display_name, icon_url = member.avatar_url)
        await ctx.send(embed=embed)

def setup(bot):
    bot.add_cog(Economy(bot))