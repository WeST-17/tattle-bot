from dotenv import load_dotenv
from os import environ
import discord
import re
from discord.ext import commands
import asyncio
from datetime import date, datetime, timedelta #date.today()

# Google Sheets API and gspread imports
import gspread

load_dotenv()

# Google Drive and Sheets API

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

# Appends complaint to database
def gcFile(sheet, accused: str, tea: str, ban: str):
    currentDate = date.today().isoformat()
    all_values = sheet.get_all_values()
    # Filter out rows with no values
    filledRows = [row for row in all_values if any(cell.strip() for cell in row)]
    sheet.append_row([currentDate, accused, tea.content, ban.content])

# Compiles complaint report for admins
def teaGet(sheet, user: str):
    complaint_values = sheet.get_all_values()
    filtered_complaints = [row for row in complaint_values if row[1] == user]
    return filtered_complaints

# increase and decrease demo time per user, for admin use only
# def demotions(sheet, userD: str):
#     user_demos = sheet.get_all_values()
#     filter_user = [row[1] for row in user_demos if row[0] == userD]
#     demo_length = 

#     return

# integer check
def is_integer(message):
    try:
        int(message.content)
        return True
    except ValueError:
        return False
    
# valid date check:
def is_valid_date(message):
    try:
        # Try to parse the message content as a date
        datetime.strptime(message.content, "%Y-%m-%d")
        return True
    except ValueError:
        return False

# Discord Bot API
TOKEN = environ.get('DISCORD_TOKEN')

def run():
    userBans = {}
    
    # Service account login for excel, can change depending on form access
    gc = gspread.service_account(filename="tattle_cred.json")
    # Opens google sheet
    tattleData = gc.open("tattleBot_Database")
    teahouseTea = tattleData.get_worksheet(0)
    demotionSheet = tattleData.get_worksheet(1)

    # Discord bot functions and commands
    intents = discord.Intents.default()
    intents.message_content = True
    intents.members = True
    
    bot = commands.Bot(command_prefix='!', intents=intents)

    @bot.event
    async def on_ready():
        print('Logged on as {0}!'.format(bot.user))

    @bot.command()
    @commands.has_any_role('Brew Tea Ful', 'Koala Tea')
    async def demote(ctx):
        await ctx.send("This command is under construction!")
        return
        '''
        Increase or decrease demotion time

        Parameters:
        - None
        Function:
        - Allows admins to increase or decrease demotion time per person. Tracked in google sheets
        
        await ctx.send("Which user's demotion time do you want to adjust? Enter 'x' to cancel.")
        try:
            user_demo = await bot.wait_for('message', timeout=60, check=lambda m: m.author == ctx.author)

            if user_demo.content.lower() == 'x':
                await ctx.send("Request canceled.")
                return
            # Extract user ID using regular expression
            user_match = re.match(r"<@!?(\d+)>", user_demo.content)
            
            if user_match:
                user_id = int(user_match.group(1))
                
                # Get the member from the guild
                member = ctx.guild.get_member(user_id)

            demotions(demotionSheet, member.global_name)

            await ctx.send("User demotion changed!")
        
        except asyncio.TimeoutError:
            await ctx.send("You took too long to respond. The data request has been canceled.")
        '''
    @bot.command()
    @commands.has_any_role('Brew Tea Ful', 'Koala Tea')
    async def compile(ctx):
        '''
        Get submissions from database in discord

        Parameters:
        - None

        Function:
        - Gets data about tea for specific 
        '''
        await ctx.send("What user data do you want to compile? Enter 'x' to cancel.")
        try:
            user_tag = await bot.wait_for('message', timeout=60, check=lambda m: m.author == ctx.author)

            # Check if the user wants to cancel
            if user_tag.content.lower() == 'x':
                await ctx.send("Request canceled.")
                return

            # Extract user ID using regular expression
            user_match = re.match(r"<@!?(\d+)>", user_tag.content)
            
            if user_match:
                user_id = int(user_match.group(1))
                
                # Get the member from the guild
                member = ctx.guild.get_member(user_id)
            
            filteredComplaints = teaGet(teahouseTea, member.global_name)

            if filteredComplaints:
                await ctx.send("Compiled Complaints: ")
                for row in filteredComplaints:
                    for data in row[1:]:
                        await ctx.send(str(data))
                    await ctx.send("----------------------")
            else:
                await ctx.send("No complaints found for this user")
        
        except asyncio.TimeoutError:
            await ctx.send("You took too long to respond. The data request has been canceled.")

    
    @bot.command()
    async def tattle(ctx):
        """
        Tattle on someone.

        Parameters:
        - None
        
        Function:
        - Asks user for user tag and message to file complaint.
        """
        await ctx.send("Who do you have tea on? Enter 'x' to cancel.")
        try:
            user_tag = await bot.wait_for('message', timeout=60, check=lambda m: m.author == ctx.author)

            # Check if the user wants to cancel
            if user_tag.content.lower() == 'x':
                await ctx.send("Complaint canceled.")
                return

            # Extract user ID using regular expression
            user_match = re.match(r"<@!?(\d+)>", user_tag.content)
            
            if user_match:
                user_id = int(user_match.group(1))
                
                # Get the member from the guild
                member = ctx.guild.get_member(user_id)

                if member:
                    user_name = member.global_name
                else:
                    user_name = f"Unknown User (ID: {user_id})"
                
                await ctx.send(f"What tea do you have about {user_tag.content}?")
                
                complaint = await bot.wait_for('message', timeout=60, check=lambda m: m.author == ctx.author)

                await ctx.send(f"How many weeks do you think the demotion should be?")

                banLength = await bot.wait_for('message', timeout=60, check=lambda m: m.author == ctx.author and is_integer(m))
                await ctx.send("Thank you for your tea. Someone will look into it.")

                gcFile(teahouseTea, user_name, complaint, banLength)
            else:
                await ctx.send("Invalid user mention.")
        except asyncio.TimeoutError:
            await ctx.send("You took too long to respond. The accusation process has been canceled.")
        except ValueError:
            await ctx.send("Invalid number. Please enter a valid number of weeks.")

    bot.run(TOKEN)

run()