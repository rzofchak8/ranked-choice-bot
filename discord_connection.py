# bot.py
import asyncio
import discord
import logging
import os
import string
from discord import app_commands, DMChannel
from dotenv import load_dotenv
from polls import create_poll, create_ballot, record_vote, close_poll, get_candidates, get_user_ballot
# from pprint import pprint

load_dotenv()
logger = logging.getLogger(__name__)
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD_ID = os.getenv('DISCORD_GUILD')
MY_GUILD= discord.Object(GUILD_ID)

class MyClient(discord.Client):
    # Suppress error on the User attribute being None since it fills up later
    user: discord.ClientUser

    def __init__(self, *, intents: discord.Intents):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    # Instead of specifying a guild to every command, we copy over our global commands instead.
    # By doing so, we don't have to wait up to an hour until they are shown to the end-user.
    async def setup_hook(self):
        self.tree.copy_global_to(guild=MY_GUILD)
        await self.tree.sync(guild=MY_GUILD)

class PollCreateView(discord.ui.View):
    def __init__(self, *, timeout = 180, poll_id):
        super().__init__(timeout=timeout)
        self.used_users = set()
        self.poll_id: int = poll_id
        
    @discord.ui.button(label='Request Ballot', style=discord.ButtonStyle.primary)
    async def request_ballot(self, interaction: discord.Interaction, button: discord.ui.Button):
        user = interaction.user
        logger.info('ballot requested by user', user.id, self.poll_id)
        
        if user.id in self.used_users:
            logger.debug('user has requested ballot more than once', user.id, self.poll_id)
            await interaction.response.send_message(
                "You already used this button.",
                ephemeral=True
            )
            return

        self.used_users.add(user.id)
        candidates = create_ballot(self.poll_id, user.id)
        
        if candidates is None:
            await interaction.response.send_message(
                "Poll no longer exists!",
                ephemeral=True
            )
            return
        
        await interaction.response.send_message(
            "Check your DMs!",
            ephemeral=True
        )

        try:
            dm = await user.create_dm()
            msg = (f'Hello! Please reply with responses for poll #**{self.poll_id}**. ' + 
                'Your votes should be in a comma-separated fashion (i.e. `a,b,c,...`). ' + 
                'You have 24 hours, or until the poll is manually closed.\n**Candidates**:\n```')
            for char, candidate in candidates.items():
                msg += f'({char}) {candidate}\n'
            msg += "```"
            embed = discord.Embed(title=f"Poll #{self.poll_id}", description=str(msg)[:4096])
            await dm.send(embed=embed)

            message_result = False
            while message_result == False:
                message_result = await await_vote(self.poll_id, user.id, interaction, dm)
            
            await dm.send("This interaction is now closed.")

        except discord.Forbidden:
            await interaction.followup.send(
                "I can't DM you. Please enable DMs.",
                ephemeral=True
            )

        except asyncio.TimeoutError:
            await dm.send("You did not reply in time. Interaction closed.")

async def await_vote(poll_id: int, user_id: int, interaction: discord.Interaction, dm: DMChannel):
    """Give user multiple attempts to vote."""
    def check(m):
        return m.author.id == interaction.user.id and m.guild is None

    reply = await interaction.client.wait_for(
        "message",
        check=check,
        timeout=60*60*24
    )
    
    res = record_vote(poll_id, user_id, reply.content.strip())
    if res is None:
        await dm.send("Either the poll is closed, or you already voted. Your last vote has not been recorded.")
        return None
    elif res is False:
        await dm.send("You have entered an invalid character, please try voting again.")
        return False
    
    user_ballot = get_user_ballot(poll_id, user_id)
    # FIXME: more reasonable vote str
    embed = discord.Embed(title=f"Poll #{poll_id} vote", description=str(f"I've recorded your ballot:\n ```{user_ballot}```")[:4096])
    await dm.send(embed=embed)
    # await dm.send(f"Your vote has been recorded!\nYou voted: **{reply.content}**")
    return True

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
)
async def poll_create(interaction: discord.Interaction, poll_title: str, poll_entries: str):
    """Creates a ranked-choice poll."""
    msg = f'\n**poll:** {poll_title}\n'
    
    poll_id = create_poll(poll_entries)
    if poll_id == -1:
        print('too many polls currently, please try again later')
        await interaction.response.send_message(msg)

    candidates = get_candidates(poll_id)
    if candidates is None:
        await interaction.response.send_message("Something went wrong when fetching candidates. Please try creating another poll.")
        return
    msg += f'**poll_id:** #{poll_id}\n```Candidates:\n\n'
    
    for i in range(len(candidates)):
        option = string.ascii_lowercase[i]
        msg += f'({option}) {candidates[i]}\n'
        
    msg += "```\n"
    embed = discord.Embed(title=f"Poll #{poll_id}", description=str(msg)[:4096])
    view = PollCreateView(poll_id=poll_id)
    await interaction.response.send_message(embed=embed, view=view)

@client.tree.command()
@app_commands.describe(
    poll_id='id of the poll to close',
)
async def poll_close(interaction: discord.Interaction, poll_id: int):
    """Closes a ranked-choice poll and returns the results."""
    result = close_poll(poll_id)
    print(result)
    embed = discord.Embed(title=f"Poll #{poll_id} Results", description=str(f"```{result}```")[:4096])
    await interaction.response.send_message(embed=embed)
    # await interaction.response.send_message(f'```{result}```')


client.run(TOKEN)

"""
TODOS:
+ change message timing limit to 24hrs

- SEPARATE OUT FUNCITONALITY INTO FILES
- LOGS
- declare return type for all our functions
+ ensure error handling is consistent (can a user re-vote after an error of some sort, etc)
- remove poll from existence after some time
+ add pretty formatting to messages:
    + poll creation message
    + final results message
- elegant shutdown
- TRY/CATCH ERROR HANDLING
"""