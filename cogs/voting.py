import discord
from discord.ext import commands

class Voting(commands.Cog):

    def __init__(self, bot):
            self.bot = bot

    def make_embed(self, title, color, options, author):

        body = ''
        for op in options:
            body += op + '\n'
        embed = discord.Embed(title=title, description=body, color=color)
        embed.set_author(name=author.display_name, icon_url=author.avatar_url)
        return embed

    @commands.command(description = '?poll <title> <option1 or color> <option2> ...')
    async def poll(self, ctx, title, *options):
        options = list(options) # convert to list to support item assignment

        if len(options) < 1:
            await ctx.send('please provide at least one option')
            return

        def rolecolor(self, ctx):
            for r in reversed(ctx.message.author.roles):
                if r.color.value > 0:
                    return r.color
            return discord.Color.random()

        color = None
        if options[0].startswith('0x') or options[0].startswith('#'):
            try:
                if options[0].startswith('#'):
                    options[0] = options[0][1:]
                color = int(options[0], 16)
                del options[0]
            except Exception:
                color = rolecolor(self, ctx)
        else:
            color = rolecolor(self, ctx)

        if len(options) > 20:
            await ctx.send('poll can\'t have more than 20 options')
            return

        embedmsg = await ctx.send(embed=self.make_embed(title, color, options, ctx.message.author))
        reactmsg = await ctx.send('react to this message with the emojis to use')

        reactions = []
        while len(reactions) < len(options):

            def check(reaction, user):
                return reaction.message == reactmsg and user == ctx.message.author

            r, user = await self.bot.wait_for('reaction_add', check=check)
            e = r.emoji

            if e in reactions:
                await ctx.send('emoji already used in this poll')
                continue

            if type(e) == discord.Emoji and not e.is_usable():
                await ctx.send('i can\'t use that emoji here :(')
                continue

            options[len(reactions)] = str(e) + ' ' + options[len(reactions)]
            reactions.append(e)
            await embedmsg.edit(embed=self.make_embed(title, color, options, ctx.message.author))
        
        await reactmsg.delete()
        await ctx.message.delete()
        for r in reactions:
            await embedmsg.add_reaction(r) 

def setup(bot):
    bot.add_cog(Voting(bot))