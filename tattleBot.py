# discord permissions integer: 1099511639040
# includes: read messages, moderate members, send messages, manage messages
from dotenv import load_dotenv
from os import environ
import discord
import re
from discord.ext import commands
import asyncio
from datetime import date #date.today()

# Google Sheets API and gspread imports
import gspread

load_dotenv()

# Google Drive and Sheets API

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

def gcFile(sheet, accused: str, tea: str):
    currentDate = date.today().isoformat()
    all_values = sheet.get_all_values()
    # Filter out rows with no values
    filledRows = [row for row in all_values if any(cell.strip() for cell in row)]
    teaID = len(filledRows)
    sheet.append_row([teaID, currentDate, accused, tea.content])

# Discord Bot API
TOKEN = environ.get('DISCORD_TOKEN')

def run():
    # Service account login for excel, can change depending on form access
    gc = gspread.service_account(filename="tattle_cred.json")
    # Opens google sheet
    teahouseTea = gc.open("tattleBot_Database").sheet1

    # Discord bot functions and commands
    intents = discord.Intents.default()
    intents.message_content = True
    intents.members = True
    
    bot = commands.Bot(command_prefix='!', intents=intents)

    @bot.event
    async def on_ready():
        print('Logged on as {0}!'.format(bot.user))

    @bot.command()
    async def tattle(ctx):
        """
        Tattle on someone.

        Parameters:
        - None
        
        Function:
        - Asks user for user tag and message to file complaint.
        """
        await ctx.send("Who you got tea on?")
        try:
            user_tag = await bot.wait_for('message', timeout=60, check=lambda m: m.author == ctx.author)

            # Extract user ID using regular expression
            user_match = re.match(r"<@!?(\d+)>", user_tag.content)
            
            if user_match:
                user_id = int(user_match.group(1))
                
                # Get the member from the guild
                member = ctx.guild.get_member(user_id)

                if member:
                    user_name = member.display_name
                else:
                    user_name = f"Unknown User (ID: {user_id})"
                
                await ctx.send(f"What tea you got about {user_tag.content}?")
                
                complaint = await bot.wait_for('message', timeout=60, check=lambda m: m.author == ctx.author)
                await ctx.send("Thank you for your tea. Someone will look into it.")

                gcFile(teahouseTea, user_name, complaint)
            else:
                await ctx.send("Invalid user mention.")
        except asyncio.TimeoutError:
            await ctx.send("You took too long to respond. The accusation process has been canceled.")

    bot.run(TOKEN)

run()