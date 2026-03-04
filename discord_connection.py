# bot.py
import os
import csv
from io import StringIO
from pprint import pprint
import discord
from discord import app_commands
from dotenv import load_dotenv
from pyrankvote import Candidate, Ballot
import random
import asyncio
from polls import create_poll

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILD')


MY_GUILD= discord.Object(GUILD)

class MyClient(discord.Client):
    # Suppress error on the User attribute being None since it fills up later
    user: discord.ClientUser

    def __init__(self, *, intents: discord.Intents):
        super().__init__(intents=intents)
        # A CommandTree is a special type that holds all the application command
        # state required to make it work. This is a separate class because it
        # allows all the extra state to be opt-in.
        # Whenever you want to work with application commands, your tree is used
        # to store and work with them.
        # Note: When using commands.Bot instead of discord.Client, the bot will
        # maintain its own tree instead.
        self.tree = app_commands.CommandTree(self)

    # In this basic example, we just synchronize the app commands to one guild.
    # Instead of specifying a guild to every command, we copy over our global commands instead.
    # By doing so, we don't have to wait up to an hour until they are shown to the end-user.
    async def setup_hook(self):
        # This copies the global commands over to your guild.
        self.tree.copy_global_to(guild=MY_GUILD)
        await self.tree.sync(guild=MY_GUILD)

class PollCreateView(discord.ui.View):
    def __init__(self, *, timeout = 180):
        super().__init__(timeout=timeout)
        self.used_users = set()
        
    @discord.ui.button(label='Request Ballot', style=discord.ButtonStyle.primary)
    async def request_ballot(self, interaction: discord.Interaction, button: discord.ui.Button):
        user = interaction.user

        # Simulated per-user disable
        if user.id in self.used_users:
            await interaction.response.send_message(
                "You already used this button.",
                ephemeral=True
            )
            return

        self.used_users.add(user.id)

        await interaction.response.send_message(
            "Check your DMs!",
            ephemeral=True
        )

        try:
            dm = await user.create_dm()
            await dm.send("Hello! Please reply with something. You have 60 seconds.")

            def check(m):
                return m.author.id == interaction.user.id and m.guild is None

            reply = await interaction.client.wait_for(
                "message",
                check=check,
                timeout=60
            )

            await dm.send(f"You said: {reply.content}")
            await dm.send("This interaction is now closed.")

        except discord.Forbidden:
            await interaction.followup.send(
                "I can't DM you. Please enable DMs.",
                ephemeral=True
            )

        except asyncio.TimeoutError:
            await dm.send("You did not reply in time. Interaction closed.")
        

intents=discord.Intents.default()
intents.message_content = True
intents.members = True
client = MyClient(intents=intents)

@client.event
async def on_ready():
    print(f'Logged in as {client.user} (ID: {client.user.id})')
    print('------')


@client.tree.command()
@app_commands.describe(
    poll_title='the title of the poll',
    poll_entries='a commma-separated list of poll options',
    randomize_ballots='randomize ballot order (default = true)',
)
async def poll_create(interaction: discord.Interaction, poll_title: str, poll_entries: str, randomize_ballots: bool = True):
    """Creates a ranked-choice poll."""
    msg = f'\n**poll:** {poll_title}\n'
    
    poll_id = create_poll()
    if poll_id == -1:
        print('too many polls currently, please try again later')
        await interaction.response.send_message(msg)

        
    poll_id = random.randrange(1000,9999)
    
    msg += f'**poll_id:** #{poll_id}'
    
    view = PollCreateView()
    await interaction.response.send_message(msg, view=view)


client.run(TOKEN)

"""
TODOS:
- create a hub for polls - dict tying id to poll ctx?
- change message timing limit to 24hrs
- close poll at 24 hrs
- parse response for user id
- create ballot for user id

- poll_close command
- create ballots
- fill in undeclared chars randomly at end of ballot
- create ballots 
- invoke pyrankvote and parse election result - show only final result

- SEPARATE OUT FUNCITONALITY INTO FILES
"""