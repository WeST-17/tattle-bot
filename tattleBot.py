from helper import *
from version_notes import version_1_3

from dotenv import load_dotenv
from os import environ
import discord
import re
from discord.ext import commands, tasks
import asyncio

# Google Sheets API and gspread imports
import gspread


load_dotenv()

# Google Drive and Sheets API

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

# Discord Bot API
TOKEN = environ.get('DISCORD_TOKEN')

admin_roles = []

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

    # Function for checking demotion periods, updating sheet, and sending updates to admins:
    # Admin list as global variable to start once at bot startup
    @tasks.loop(hours=24, reconnect=True)
    async def demotionUpdate(channel):
        userDemoUpdate = autoDemoUpdate(demotionSheet)
        if userDemoUpdate:
            updateMessage = ""
            for item in userDemoUpdate:
                updateMessage += f"@{item}\n"

            if channel:
                await channel.send(admin_roles[0].mention)
                embededUpdate = discord.Embed(title=f"Users to Remove from the Cup of Shame:", description=updateMessage, color=0xaeffff)
                await channel.send(embed=embededUpdate)
        
        await asyncio.sleep(86400)  # Sleep for 24 hours before the next iteration

    async def getAdmin(guild):
        global admin_roles
        admin_roles = [role for role in guild.roles if role.permissions.administrator]

    @demotionUpdate.before_loop
    async def before_demotion_update():
        await bot.wait_until_ready()

    @bot.event
    async def on_ready():
        channel = discord.utils.get(bot.get_all_channels(), name="teahouse-tattles")
        await getAdmin(channel.guild)
        demotionUpdate.start(channel)
        print('Logged on as {0}!'.format(bot.user))
    

    @bot.command()
    async def version(ctx):
        '''
        See latest version notes.
        '''
        await ctx.send(version_1_3)
        return

    @bot.command()
    async def menu(ctx):
        '''
        Check what commands are available.
        '''
        helpMessage = (
            f"--- Help Menu ---\n"
            f"!menu\n"
            f"!version\n\n"
            f"--- General Commands ---\n"
            f"!tattle\n"
            f"!check @[user tag]\n\n"
            f"--- Admin Commands ---\n"
            f"!demote @[user tag]\n"
            f"!compile @[user tag]\n"
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
        # Get user tag of command author:
        teaAuthor = ctx.message.author.name

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
                await ctx.send("Thank you for your tea. Someone will look into it. You can include evidence below:")

                gcFile(teahouseTea, user_name, complaint, banLength, teaAuthor)
            else:
                await ctx.send("Invalid user mention.")
        except asyncio.TimeoutError:
            await ctx.send("You took too long to respond. The accusation process has been canceled.")
        except ValueError:
            await ctx.send("Invalid number. Please enter a valid number of weeks.")
            

    # check demotion period and weeks left
    @bot.command()
    async def check(ctx, user_tag: str):
        '''
        Check demotion period and weeks left.
        '''
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

            if len(user_demo_check) == 0:
                await ctx.send("There is no active demotion period for this user.")
                return

            for row in user_demo_check:
                message = (
                    f"Remaining weeks of demotion: {row[1]}\n"
                    f"Last day of demotion: {row[2][:10]}"
                )
                embedCheck = discord.Embed(title=f"Current Demotion Period for {member.display_name}", description=message, color=0xaeffff)
                await ctx.send(embed=embedCheck)
        else:
            await ctx.send("Invalid user mention. Please use '@' to find a user.")

    # Admin command, update database and demote user role
    @bot.command()
    @commands.has_guild_permissions(administrator=True)
    async def demote(ctx, user_tag: str):
        '''
        Update demotion period for a user. Add user to Cup of Shame(Under Construction).

        Parameters:
        - None
        Function:
        - Allows admins to add 'Cup of Shame' demotion role per person. Can adjust amount of time. Tracked in google sheets(?)
        '''
        # demote_role = discord.utils.get(ctx.guild.roles, name="Cup of Shame")

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
                demoWeeksAdd = await bot.wait_for('message', timeout=60, check=lambda m: m.author == ctx.author and is_integer(m))

                if demoWeeksAdd.content.lower() == 'x':
                    await ctx.send("Complaint canceled.")
                    return

                # Call function to update Google Sheet database
                adjustDemotion = demotion(demotionSheet, user_name, int(demoWeeksAdd.content))

                await ctx.send(adjustDemotion)
            
            else:
                await ctx.send("Invalid user mention. Please use '@' to find a user.")
        
        except asyncio.TimeoutError:
            await ctx.send("You took too long to respond. The data request has been canceled.")
        except ValueError:
            await ctx.send("Invalid number. Please enter a valid number of weeks.")

     
    @bot.command()
    @commands.has_guild_permissions(administrator=True)
    async def compile(ctx, user_tag: str):
        '''
        Get submissions from database in discord.

        Parameters:
        - None

        Function:
        - Gets data about tea for specific 
        '''
        try:
            user_match = re.match(r"<@!?(\d+)>", user_tag)
            
            if user_match:
                user_id = int(user_match.group(1))
                
                # Get the member from the guild
                member = ctx.guild.get_member(user_id)
            else:
                await ctx.send("User not found...")
                return
            
            filteredComplaints = teaGet(teahouseTea, member.global_name)

            if filteredComplaints:
                message = "----------------------\n"
                for row in filteredComplaints:
                    complaint = (
                        f"Date: {row[1]}\n"
                        f"Tea: {row[2]}\n"
                        f"Demotion Length Request: {row[3]}\n"
                        f"----------------------\n")
                    message += complaint
                embed = discord.Embed(title=f"Compiled Complaints for {member.display_name}", description=message, color=0xaeffff)
                await ctx.send(embed=embed)
            else:
                await ctx.send("No complaints found for this user")
                return
        
        except asyncio.TimeoutError:
            await ctx.send("You took too long to respond. The data request has been canceled.")

    bot.run(TOKEN)

run()

