import discord
from discord.ext import commands
from PIL import Image, ImageDraw, ImageFont
from dotenv import load_dotenv
import aiohttp
import io
import os
import logging

# Load .env variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)

# Setup bot
intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")

@bot.event
async def on_member_join(member):
    base = Image.open("template.png").convert("RGBA")

    # Download avatar
    async with aiohttp.ClientSession() as session:
        async with session.get(str(member.display_avatar.url)) as resp:
            avatar_bytes = await resp.read()

    avatar = Image.open(io.BytesIO(avatar_bytes)).convert("RGBA")
    avatar = avatar.resize((293, 293))

    # Create circular cropped avatar
    circular_avatar = Image.new("RGBA", (293, 293), (0, 0, 0, 0))
    mask = Image.new("L", (293, 293), 0)
    draw_mask = ImageDraw.Draw(mask)
    draw_mask.ellipse((0, 0, 293, 293), fill=255)
    circular_avatar.paste(avatar, (0, 0), mask)

    # Paste on template at exact position
    base.paste(circular_avatar, (218, 108), circular_avatar)

    # Draw username below avatar
    draw = ImageDraw.Draw(base)
    try:
        font = ImageFont.truetype("arial.ttf", 40)
    except IOError:
        font = ImageFont.load_default()

    username_text = f"@{member.name}"
    bbox = draw.textbbox((0, 0), username_text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    text_x = 218 + (293 - text_width) // 2
    text_y = 108 + 293 + 28

    # Shadow + main text
    draw.text((text_x + 2, text_y + 2), username_text, font=font, fill="black")
    draw.text((text_x, text_y), username_text, font=font, fill="white")

    # Save output to buffer
    output = io.BytesIO()
    base.save(output, format="PNG")
    output.seek(0)

    # Send to welcome channel
    for channel in member.guild.text_channels:
        if "welcome" in channel.name:
            await channel.send(
                f"👋 Welcome {member.mention} to **Play 2 Win**!",
                file=discord.File(fp=output, filename="welcome.png")
            )
            break

# Run the bot with token from .env
bot.run(os.getenv("DISCORD_BOT_TOKEN"))
