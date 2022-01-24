import os
import random
from PIL import Image,ImageFont,ImageDraw,ImageOps
from io import BytesIO
import csv
import ast
import textwrap
import discord
from discord.ext import commands
import asyncio
import string

class FontGame(commands.Cog):

    width = 40
    img_size = (800, 600)
    margin = 100

    easyxp = 10
    medxp = 50
    hardxp = 100

    mediumdir = '../fonts-less/'
    harddir = '../fonts/'
    easydir = '../easyfonts/'
    fontdir = easydir

    lyricdir = '../lyrics-copy/'
    lyricbackupdir = '../lyrics/'
    tweetdir = '../tweets.csv'

    percent = len(os.listdir(lyricbackupdir)) // 10
    percent = percent if percent > 1 else 1
    
    type = 'lyrics' #can hold value 'tweets' or 'lyrics'

    bitecoinid1 = 471481060664934400
    bitecoinid2 = 930607047538536488

    def __init__(self, bot):
        self.bot = bot

    # https://stackoverflow.com/a/47742159
    def _parse_bytes(self, field):
        """ Convert string represented in Python byte-string literal b'' syntax into
            a decoded character string - otherwise return it unchanged.
        """
        result = field
        try:
            result = ast.literal_eval(field)
        finally:
            return result.decode() if isinstance(result, bytes) else field

    def my_csv_reader(self, filename, /, **kwargs):
        with open(filename, 'rt', newline='') as file:
            for row in csv.reader(file, **kwargs):
                yield [self._parse_bytes(field) for field in row]

    def rand_tweet(self):
        reader = self.my_csv_reader(self.tweetdir)
        randrow = random.choice(list(reader))
        while 'https://' in randrow[1] or randrow[1].startswith('@'): # exclude boring tweets
            reader = self.my_csv_reader(self.tweetdir)
            randrow = random.choice(list(reader))
        return (randrow[0], randrow[1])

    def get_file_with_extension(self, directory, extensions):
        file = random.choice(os.listdir(directory))
        extension = file[-3:].lower()
        while extension not in extensions: # make sure file is valid
            file = random.choice(os.listdir(directory))
            extension = file[-3:].lower()
        return file

    def rand_lyric(self):
        if len(os.listdir(self.lyricdir)) < self.percent: # don't go all the way to 0 in case there's some really long songs
            for file in os.listdir(self.lyricbackupdir):
                backupfile = open(self.lyricbackupdir+file, 'r')
                copyfile = open(self.lyricdir+file, 'w')
                if file != '.DS_Store':
                    copyfile.write(backupfile.read())

        filename = self.get_file_with_extension(self.lyricdir, ['txt'])
        text = ''
        with open(self.lyricdir+filename, 'r') as f:
            try:
                text = f.read()
            except UnicodeDecodeError:
                return('ERROR', 'error reading file %s' % self.lyricdir+filename)
        verses = text.split('\n\n')
        song = verses[0]
        index = random.randrange(1, len(verses))
        lyric_t = (song, verses[index])

        # remove used lyrics to reduce repeats
        del verses[index]
        with open(self.lyricdir+filename, 'w') as f:
            f.write('\n\n'.join(verses))
        if len(verses) == 1:
            os.remove(self.lyricdir+filename)

        return lyric_t

    def max_line_width(self, text_arr, font):
        max = 0
        for line in text_arr:
            size = font.getsize(line)[0]
            if size > max:
                max = size
        return max

    def get_fontsize(self, text_arr, fontpath):
        size = 1
        font = ImageFont.truetype(fontpath, size)
        lineheight = font.getsize(text_arr[0])[1]
        linewidth = self.max_line_width(text_arr, font)
        while linewidth < (self.img_size[0] - self.margin) and (lineheight < self.img_size[1] - self.margin):
            size += 1
            font = ImageFont.truetype(fontpath, size)
            lineheight = font.getsize(text_arr[0])[1]
            linewidth = self.max_line_width(text_arr, font)
        return size

    def get_auth_fontsize(self, text, fontpath, startsize):
        size = startsize
        font = ImageFont.truetype(fontpath, size)
        linewidth = font.getsize(text)[0]
        while linewidth > (self.img_size[0] - self.margin):
            size -= 1
            font = ImageFont.truetype(fontpath, size)
            linewidth = font.getsize(text)[0]
        return size

    def rand_colors(self):
        h = random.randrange(360)
        s = 90
        l = 40
        return ('hsl({},{}%,{}%)'.format(h,s,l))

    def get_coords(self, text_arr, font):
        totalheight = 0
        for line in text_arr:
            totalheight += font.getsize(line)[1]
        linewidth = self.max_line_width(text_arr, font)
        x = (self.img_size[0] - linewidth) // 2
        y = (self.img_size[1] - totalheight) // 2
        return (x, y)

    def get_fontname(self, font_file):
        name = font_file[:-4]
        chars = ['-', '[', '_']
        for c in chars:
            index = name.find(c)
            if index != -1:
                name = name[:index]
        newname = ''
        for i in range(len(name)):
            if i > 0 and name[i].isupper() and name[i-1].islower():
                newname += ' ' + name[i]
            else:
                newname += name[i]
        return newname

    async def give_money(self, msg):
        economy = self.bot.get_cog('Economy')
        if economy is not None:
            bc = 0
            xp = 0
            if self.fontdir == self.easydir:
                xp = self.easyxp
            elif self.fontdir == self.mediumdir:
                xp = self.medxp
            elif self.fontdir == self.harddir:
                xp = self.hardxp
            bc = xp * 10
            bc1 = self.bot.get_emoji(self.bitecoinid1)
            bc2 = self.bot.get_emoji(self.bitecoinid2)
            bc_emoji = bc1 if bc1 != None else bc2
            if bc_emoji == None:
                bc_emoji = 'bitecoin'
            await msg.reply('you got it! good job +%d %s +%d xp' % (bc, bc_emoji, xp))
            await economy.add_coins(msg.author, msg.channel, bc)
            await economy.add_exp(msg.author, msg.channel, xp)
        else:
            await msg.reply('you got it! good job')

    @commands.command()
    async def fame(self, ctx):
        font_file = self.get_file_with_extension(self.fontdir, ['otf', 'ttf'])
        fontpath = self.fontdir+font_file

        author, text = ('','')
        if self.type == 'tweets':
            author, text = self.rand_tweet()
        elif self.type == 'lyrics':
            author, text = self.rand_lyric()
        else:
            await ctx.send('error: invalid type')
            return

        wrapped_text = []
        for line in text.split('\n'):
            wrapped_line = textwrap.wrap(line, width=self.width, replace_whitespace=False)
            for l in wrapped_line:
                wrapped_text.append(l)

        fontsize = 0
        try:
            fontsize = self.get_fontsize(wrapped_text, fontpath)
        except OSError:
            await ctx.send('error reading file %s' % fontpath)
            return 

        font = ImageFont.truetype(fontpath, fontsize)
        bkg_color = self.rand_colors()
        font_color = "#ffffff"

        img = Image.new('RGB', self.img_size, bkg_color)
        draw = ImageDraw.Draw(img)

        (x, y) = self.get_coords(wrapped_text, font)
        lineheight = font.getsize(wrapped_text[0])[1]
        for line in wrapped_text:
            draw.text((x, y), line, font=font, fill=font_color)
            y += lineheight


        auth_size = fontsize - 10 if fontsize - 10 > 10 else 10
        auth_size = self.get_auth_fontsize(author, fontpath, auth_size)

        auth_font = ImageFont.truetype(fontpath, auth_size)
        auth_x = self.get_coords([author], auth_font)[0]
        auth_y = self.img_size[1] - self.margin
        draw.text((auth_x, auth_y), author, font=auth_font, fill=font_color)

        output = BytesIO()
        img.save(output, format='png')
        output.seek(0)
        await ctx.reply(file=discord.File(output, filename='text.png'), mention_author=False)

        fontname = self.get_fontname(font_file)

        def check(msg):
            cleanmsg = msg.content.lower().translate(str.maketrans('', '', string.punctuation))
            cleanfile = fontname.lower().translate(str.maketrans('', '', string.punctuation))
            return msg.channel == ctx.channel and (cleanmsg == cleanfile or msg.content == 'skip')

        print(fontname)

        try:
            answer = await self.bot.wait_for('message', timeout=20, check=check)
            if answer.content == 'skip':
                await ctx.send('the font is '+fontname)
            else:
                await self.give_money(answer)
        except asyncio.TimeoutError:
                await ctx.send('too slow it was '+fontname)

    @commands.command()
    async def setmode(self, ctx, mode):
        if mode == 'easy':
            if self.fontdir == self.easydir:
                await ctx.send('game already in easy mode!')
            else:
                self.fontdir = self.easydir
                await ctx.send('mode set to easy')
        elif mode == 'medium':
            if self.fontdir == self.mediumdir:
                await ctx.send('game already in medium mode!')
            else:
                self.fontdir = self.mediumdir
                await ctx.send('mode set to medium')
        elif mode == 'hard':
            if self.fontdir == self.harddir:
                await ctx.send('game already in hard mode!')
            else:
                self.fontdir = self.harddir
                await ctx.send('mode set to hard')
        else:
            await ctx.send('invalid mode. please choose either easy, medium, or hard')

    @commands.command()
    async def settype(self, ctx, type):
        if type not in ['lyrics', 'tweets']:
            await ctx.send('invalid type. please choose either lyrics or tweets')
        else:
            if type == self.type:
                await ctx.send('game type is already %s!' % self.type)
            else:
                self.type = type
                await ctx.send('game type set to %s' % self.type)

def setup(bot):
    bot.add_cog(FontGame(bot))