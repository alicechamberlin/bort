import discord
from discord.ext import commands
import datetime
import json
import requests

class Anime(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    async def request_page(self, name, page, per_page):

        query = '''
        query ($page: Int, $perPage: Int, $search: String) {
            Page (page: $page, perPage: $perPage) {
                pageInfo {
                    total
                    currentPage
                    lastPage
                    hasNextPage
                    perPage
                }
                media (search: $search) {
                    id
                    title {
                        romaji
                    }
                            format
                            siteUrl
                            coverImage {
                                extraLarge
                                color
                            }
                            description (asHtml:false)
                            popularity
                            averageScore
                            tags {
                                name
                                isMediaSpoiler
                            }
                            genres
                            nextAiringEpisode {
                                episode
                                timeUntilAiring
                            }
                            status
                            season
                            seasonYear
                            episodes
                            chapters
                }
            }
        }
        '''
        variables = {
            'search': name,
            'page': page,
            'perPage': per_page
        }
        url = 'https://graphql.anilist.co'

        response = requests.post(url, json={'query': query, 'variables': variables})
        results = json.loads(response.text)

        return results

    async def generate_page_embed(self, search, results):
        page = results['data']['Page']['pageInfo']['currentPage']
        total_pages = results['data']['Page']['pageInfo']['lastPage']
        per_page = results['data']['Page']['pageInfo']['perPage']

        embed = discord.Embed(title = 'Page {}/{}'.format(page, total_pages), color=0x20e0f0)
        body = ''

        num_results = len(results['data']['Page']['media'])

        for i in range(min(per_page, num_results)):
            result = results['data']['Page']['media'][i]
            title = '{} ({})'.format(result['title']['romaji'], result['format'].lower())
            body += str(i + 1) + ') ' + title + '\n'
        
        if num_results == 0:
            body = 'No results.'
        
        embed.add_field(name = 'Showing results for: {}'.format(search), value = body)

        return embed

    async def generate_media_embed(self, item):
        title = item['title']['romaji']
        url = item['siteUrl']
        color = item['coverImage']['color']
        mediatype = item['format'].lower()

        if item['description']:
            desc = item['description'].replace('<br>', '').replace('<i>', '*').replace('</i', '*')
        else:
            desc = ''
        if len(desc) > 297:
            desc = desc[:297] + '...'

        embed_col = int(color[1:], base=16) if color else 0x20e0f0

        embed = discord.Embed(title = '{} ({})'.format(title, mediatype), description = desc, url = url, color = embed_col)

        embed.set_thumbnail(url = item['coverImage']['extraLarge'])
        if item['season'] and item['seasonYear']:
            embed.add_field(name = 'season', value = item['season'].lower() + ' ' + str(item['seasonYear']))
        if item['popularity']:
            embed.add_field(name = 'popularity', value = '#{}'.format(item['popularity']))

        if item['nextAiringEpisode']:
            ep = item['nextAiringEpisode']['episode']
            time = item['nextAiringEpisode']['timeUntilAiring']
            d = time // 86400
            h = (time - d*86400) // 3600
            m = (time - d*86400 - h*3600) // 60
            s = (time - d*86400 - h*3600 - m*60)
            desc = '{}d {}h {}m {}s'.format(d, h, m, s)
            embed.add_field(name = 'ep {} airing'.format(ep), value = desc)

        if item['averageScore']:
            embed.add_field(name = 'average score', value = '{}%'.format(item['averageScore']))
        if item['episodes']:
            embed.add_field(name = 'episodes', value = item['episodes'])
        if item['chapters']:
            embed.add_field(name = 'chapters', value = item['chapters'])

        if item['genres'] and len(item['genres']) > 0:
            embed.add_field(name = 'genres', value = ', '.join(map(lambda i: i.lower(), item['genres'])))

        tags = []
        if item['tags'] and len(item['tags']) > 0:
            i = 0
            while len(tags) < 3 and i < len(item['tags']):
                if not item['tags'][i]['isMediaSpoiler']: 
                    tags.append(item['tags'][i]['name'].lower())
                i += 1
            embed.add_field(name = 'tags', value = ', '.join(tags))

        print(json.dumps(item, indent=4))
        for field in embed.fields:
            print(field)

        return embed

    @commands.command()
    async def search(self, ctx, *, name):
        PER_PAGE = 5
        page = 1

        results = await self.request_page(name, page, PER_PAGE)
        page_embed = await self.generate_page_embed(name, results)
        page_mes = await ctx.send(embed=page_embed)

        def check(m):
            if m.author != ctx.message.author:
                return False
            if m.content == 'n':
                return True
            try:
                n = int(m.content)
                return 1 <= n <= PER_PAGE
            except ValueError:
                return False
        
        select = await self.bot.wait_for('message', check=check)

        while select.content == 'n':
            try:
                await select.delete()
            except Exception:
                pass
    
            page = page % results['data']['Page']['pageInfo']['lastPage'] + 1
            results = await self.request_page(name, page, PER_PAGE)
            page_embed = await self.generate_page_embed(name, results)

            try: 
                await page_mes.edit(embed=page_embed)
            except Exception:
                page_mes = await ctx.send(embed=page_embed)

            select = await self.bot.wait_for('message', check=check)
            
        try:
            await select.delete()
        except Exception:
            pass

        anime = results['data']['Page']['media'][int(select.content) - 1]

        anime_embed = await self.generate_media_embed(anime)

        await page_mes.edit(embed=anime_embed)



    @commands.command()
    async def next(self, ctx, *, name):
        query = '''
            query ($search: String) {
                Media (search: $search, type: ANIME) {
                    title {
                        romaji
                    }
                    nextAiringEpisode {
                        timeUntilAiring
                    }
                }
            }
        '''
        variables = {
            'search': name,
        }
        url = 'https://graphql.anilist.co'

        response = requests.post(url, json={'query': query, 'variables': variables})
        results = json.loads(response.text)

        title = results['data']['Media']['title']['romaji']
        desc = 'Not currently airing.'
        if results['data']['Media']['nextAiringEpisode'] != None:
            time_until = results['data']['Media']['nextAiringEpisode']['timeUntilAiring']
            d = time_until // 86400
            h = (time_until - d*86400) // 3600
            m = (time_until - d*86400 - h*3600) // 60
            s = (time_until - d*86400 - h*3600 - m*60)
            desc = 'Next episode in {}d {}h {}m {}s'.format(d, h, m, s)

        embed = discord.Embed(title = title, description = desc, color = 0x20e0f0)

        await ctx.send(embed = embed)

def setup(bot):
    bot.add_cog(Anime(bot))