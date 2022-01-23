from PIL import Image,ImageFont,ImageDraw,ImageOps
import random
import glob
import math
import operator
import discord
from discord.ext import commands
from io import BytesIO

# credit: gunwoo
class Spinner(commands.Cog):

	MEDIA_DIR = "media/spin"

	# credit: allison
	font = ImageFont.truetype(MEDIA_DIR + "/fonts/arial.ttf", 24);
	font_comic = ImageFont.truetype(MEDIA_DIR + "/fonts/comic.ttf", 80);
	font_impact = ImageFont.truetype(MEDIA_DIR + "/fonts/impact.ttf", 80);

	ENDING_RANDOM_FONT = True;

	# credit: allison
	colors = [(0, 93, 255),
			(35, 181, 211),
			(223, 224, 226),
			(204, 201, 220),
			(134, 231, 184),
			(241, 222, 222),
			(178, 255, 168)] #(68, 52, 79),

	jenn_color = (0, 93, 255);
	discord_color = (54, 57, 62);

	fps = 20;

	timestep = 1/fps;

	pronouns = ["he/him",
	"she/her",
	"they/them",
	"he/she/they",
	"he/she",
	"he/they",
	"she/they",
	"any",
	"ze/zir",
	"ze/hir",
	"xe/xem"]

	yesno = ["yes", "no"];

	window_size = (500,600);
	wheel_radius = 230;
	wheel_center = (wheel_radius,wheel_radius);
	wheel_center_window = (window_size[0]/2,250);

	im_num = 0;

	"""
	img = Image.open("white.png")

	draw = ImageDraw.Draw(img)

	text = "hello"

	draw.text((0,150), text)
	img.save("text.png")
	"""

	def __init__(self, bot):
		self.bot = bot;

	def lerp(self, a,b,t):
		return a + t*(b-a);

	def create_vector(self, length, angle):
		return (length * math.cos(math.radians(angle)), length * math.sin(math.radians(angle)))

	def sign(self, a):
		if a < 0: return -1;
		if a > 0: return 1;
		return 0;

	def random_rgb(self):
		#return (random.randint(50,70),random.randint(50,70),random.randint(100,255));
		return random.choice(self.colors);

	@commands.command()
	async def spin(self, ctx, *words):
		async with ctx.channel.typing():
			frames = [];
			angle = 0;
			delta = 0;
			prev = 0;
			time = 0;

			duration = random.uniform(4,6);
			totalruns = 360 * 10;
			outcomeangle = random.uniform(0,360);
			startangle = 0;
			endangle = totalruns + outcomeangle;

			if len(words) == 0:
				words = self.pronouns;
			elif len(words) == 1 and (words[0] == 'yesno' or words[0] == 'yn'):
				words = self.yesno;

			# create wheel
			wheel = Image.new('RGBA', (self.wheel_radius*2,self.wheel_radius*2), (0,0,0,0));
			draw = ImageDraw.Draw(wheel);

			draw.ellipse((0,0,self.wheel_radius*2,self.wheel_radius*2), fill=self.random_rgb(), outline='black');
			wheel_anglestep = 360/len(words);

			# draw random colored wheel
			pocket = self.colors.copy();
			random.shuffle(pocket);
			for num in range(len(words)):
				# refill the pocket
				if (len(pocket) == 0):
					pocket = self.colors.copy();
					random.shuffle(pocket);
				
				color = pocket.pop(0);
				wheel_angle = wheel_anglestep * num;
				draw.pieslice((0,0,self.wheel_radius*2,self.wheel_radius*2), wheel_angle, 360, fill=color, outline='black');

			# draw lines and words
			for num in range(len(words)):
				wheel_angle = wheel_anglestep * num;

				# draw lines
				v1 = self.create_vector(self.wheel_radius, wheel_angle);

				line_end = tuple(map(operator.add, self.wheel_center, v1)); # element wise operation, self.wheel_center + v1

				draw.line(self.wheel_center + line_end, width=2, fill='black');

				# create rotated text
				txt = words[num];
				text_angle = wheel_angle + wheel_anglestep/2;

				text = Image.new('L', (self.font.getsize(txt)));
				drawtext = ImageDraw.Draw(text);
				drawtext.text((0,0), txt, fill=255, font=self.font);
				text = text.rotate(-text_angle, expand=1);
				
				# get some data about the flipped image
				text_width = text.size[0];
				text_height = text.size[1];
				image_diagonal = math.sqrt(text_width * text_width + text_height * text_height);

				# adjust the vector based on the image
				vector_size = (self.wheel_radius/2) + (image_diagonal/4);

				v2 = self.create_vector(vector_size, text_angle);
				coords = tuple(map(operator.add, self.wheel_center, v2));

				coords = (coords[0] - text_width/2, coords[1] - text_height/2);
				coords = (int(coords[0]), int(coords[1]));

				wheel.paste(ImageOps.colorize(text, (0,0,0), (0,0,0)), 
							box=coords, mask=text);

			# create overlay
			triangle_size = (100,40);
			triangle = Image.new('L', triangle_size);
			draw_triangle = ImageDraw.Draw(triangle);
			draw_triangle.polygon([(0, triangle_size[1]/2), (triangle_size[0], 0), triangle_size], fill=255);
			triangle_coords = (int(self.wheel_center[0] + self.wheel_radius * 0.9), int(self.wheel_center[1]));

			overlay = Image.new('RGBA', self.window_size, (0,0,0,0));
			overlay_draw = ImageDraw.Draw(overlay);
			overlay.paste(ImageOps.colorize(triangle, (0,0,0), (255,53,184)), box=triangle_coords, mask=triangle);

			overlay_mask = Image.new('L', self.window_size);
			overlay_mask_draw = ImageDraw.Draw(overlay_mask);
			overlay_mask.paste(triangle, box=triangle_coords, mask=triangle);

			# create background
			background = Image.new('RGBA', self.window_size, self.discord_color + (255,));

			# create wheel mask
			wheel_mask = Image.new('L',(self.wheel_radius*2, self.wheel_radius*2));
			draw = ImageDraw.Draw(wheel_mask);
			draw.ellipse((0, 0, self.wheel_radius*2, self.wheel_radius*2), fill=255);

			# background.paste(wheel, box=(20,20), mask=wheel_mask);
			# background.paste(overlay, box=(0,0), mask=overlay_mask);

			# background.paste(overlay);
			# background.save("background.png");
			# background.show();

			# draw.line((20, 250, 480, 250), width=5, fill='black');

			# exit();

			# generate frames

			wheel_offset = (int(self.wheel_center_window[0] - (wheel.size[0]/2)), int(self.wheel_center_window[1] - (wheel.size[1]/2)));

			# initial wait

			curtains = [Image.open(self.MEDIA_DIR + "/curtain0.png"),
						Image.open(self.MEDIA_DIR + "/curtain1.png"),
						Image.open(self.MEDIA_DIR + "/curtain2.png")];

			# resize curtains
			index = 0;
			for im in curtains:
				curtains[index] = curtains[index].resize(self.window_size);
				index = index + 1;

			initial_animation_duration = int(1 * self.fps);
			curtain_time_step = initial_animation_duration / len(curtains);
			for i in range(initial_animation_duration):
				# draw the triangle
				frame = background.copy();
				wheel_instance = wheel.copy();

				frame.paste(wheel_instance, box=wheel_offset, mask=wheel_mask);
				frame.paste(overlay, mask=overlay_mask);

				curtain = curtains[int(i // curtain_time_step)];

				frame = Image.alpha_composite(frame, curtain);

				frames.append(frame);

			# start spinning
			while time < duration:

				# calculate angle
				# lerp magic op
				t = time/duration;
				t = t * t * (3 - 2 * t); # TODO: bezier curve
				angle = self.lerp(startangle, endangle, t);

				# create frame
				frame = background.copy();
				wheel_instance = wheel.rotate(angle=angle,resample=Image.BICUBIC);

				frame.paste(wheel_instance, box=wheel_offset, mask=wheel_mask);
				frame.paste(overlay, mask=overlay_mask);

				frames.append(frame);

				# debug shit
				delta = angle - prev;
				prev = angle;

				time = time + self.timestep;


			# determine outcome
			dr = 360/len(words);
			outcome = outcomeangle // dr;
			outcome = int(outcome);

			# some extra frames at the end
			wheel_instance_final = wheel.rotate(angle=angle,resample=Image.BICUBIC);
			confetti = Image.open(self.MEDIA_DIR + "/confetti.png");
			confetti_resized = confetti.resize(self.window_size);

			if self.ENDING_RANDOM_FONT:
				final_font = random.choice([self.font_impact, self.font_comic]);
			else:
				final_font = self.font;

			final_animation_duration = 2 * self.fps;
			for i in range(int(final_animation_duration)):
				frame = background.copy();
				
				confetti_frame = Image.new('RGBA', self.window_size);
				y_start = -self.window_size[1];
				y_target = self.window_size[1];
				yy = self.lerp(y_start, y_target, (i+1)/final_animation_duration);
				yy = int(yy);

				confetti_frame.paste(confetti_resized, box=(0,yy));

				frame.paste(wheel_instance_final, box=wheel_offset, mask=wheel_mask);
				frame.paste(overlay, mask=overlay_mask);
				frame = Image.alpha_composite(frame, confetti_frame);

				draw = ImageDraw.Draw(frame);
				draw.text((250, 600), words[outcome], font=final_font, anchor='mb');

				frames.append(frame);

			# create gif
			# credit: https://www.youtube.com/watch?v=aoeq5CBBBUk&ab_channel=PythonProgrammi and colin thx colin
			# this is where the image should be send to the chat by the bot.
			output = BytesIO();
			frames[0].save(output, format='GIF',
							append_images=frames[1:],
							save_all=True,	
							duration=1000/self.fps);
			
			output.seek(0);
		await ctx.reply(file=discord.File(output, filename='spinnnn.gif'), mention_author=False);
		#self.im_num += 1;

def setup(bot):
    bot.add_cog(Spinner(bot));