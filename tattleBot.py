from helper import *
from dotenv import load_dotenv
from os import environ
import discord
import re
from discord.ext import commands
import asyncio

# Google Sheets API and gspread imports
import gspread


load_dotenv()

# Google Drive and Sheets API

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

# Discord Bot API
TOKEN = environ.get('DISCORD_TOKEN')

def run():
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
    async def menu(ctx):
        helpMessage = (
            f"--- Help Menu ---\n\n"
            f"--- Commands ---\n"
            f"!tattle\n"
            f"!check @[user-tag]\n\n"
            f"--- Admin Commands ---\n"
            f"!demote\n"
            f"!compile\n"
        )

        await ctx.send(helpMessage)
        return

    @bot.command()
    async def tattle(ctx):
        """
        Tattle on someone.

        Parameters:
        - None
        
        Function:
        - Asks user for user tag and message to file complaint.
        """
        await ctx.send("Who do you have tea on? Use '@' to find a user. Enter 'x' to cancel.")
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
                    await ctx.send("This user does not exist...")
                    return
                
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

    # check demotion period and weeks left
    @bot.command()
    async def check(ctx, user_tag: str):
        # Extract user ID using regular expression
        user_match = re.match(r"<@!?(\d+)>", user_tag)

        if user_match:
            user_id = int(user_match.group(1))

            # Get the member from the guild
            member = ctx.guild.get_member(user_id)

            if member:
                user_name = member.global_name
            else:
                user_name = f"Unknown User (ID: {user_id})"

            # Call demoCheck with the user_name
            user_demo_check = demoCheck(demotionSheet, user_name)

            for row in user_demo_check:
                message = (
                    f"Name: {row[0]}\n"
                    f"Remaining weeks of demotion: {row[1]}\n"
                    f"Last day of demotion: {row[2]}"
                )
                await ctx.send(message)
        else:
            await ctx.send("Invalid user mention. Please use '@' to find a user.")

    @bot.command()
    #@commands.has_any_role('Brew Tea Ful', 'Koala Tea')
    async def demote(ctx, user_tag: str):
        '''
        Add a role to a member for a specified period of time.

        Parameters:
        - None
        Function:
        - Allows admins to add 'Cup of Shame' demotion role per person. Can adjust amount of time. Tracked in google sheets(?)
        '''     
        try:
            # Extract user ID using regular expression
            user_match = re.match(r"<@!?(\d+)>", user_tag)

            if user_match:
                user_id = int(user_match.group(1))

                # Get the member from the guild
                member = ctx.guild.get_member(user_id)

                if member:
                    user_name = member.global_name
                else:
                    user_name = f"Unknown User (ID: {user_id})"

                await ctx.send("How many demotion weeks should be added? Enter 'x' to cancel.")
                if user_tag.content.lower() == 'x':
                    await ctx.send("Complaint canceled.")
                    return

                demoWeeksAdd = await bot.wait_for('message', timeout=60, check=lambda m: m.author == ctx.author and is_integer(m) or is_valid_date(m))
                adjustDemotion = demotion(demotionSheet, member.global_name, demoWeeksAdd)

                await ctx.send(adjustDemotion)
            
            else:
                await ctx.send("Invalid user mention. Please use '@' to find a user.")
        
        except asyncio.TimeoutError:
            await ctx.send("You took too long to respond. The data request has been canceled.")
        except ValueError:
            await ctx.send("Invalid number. Please enter a valid number of weeks.")
        
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
                await ctx.send("----------------------")
                for row in filteredComplaints:
                    for data in row:
                        await ctx.send(str(data))
                    await ctx.send("----------------------")
            else:
                await ctx.send("No complaints found for this user")
        
        except asyncio.TimeoutError:
            await ctx.send("You took too long to respond. The data request has been canceled.")

    bot.run(TOKEN)

run()

