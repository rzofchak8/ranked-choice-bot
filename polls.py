import random
import string
import pyrankvote
import threading
from pyrankvote import Candidate, Ballot

poll_hub: dict[int, Poll] = {}

class Poll():
    def __init__(self, id):
        self.id: int = id
        # whether the poll is still active and able to be voted on
        self.active: bool = True
        # pyrankvote.Candidates list
        self.candidates: list[Candidate] = []
        # dictionary mapping user id to Voter
        self.voters: dict[int, Voter] = {}
        self.result = ''
        threading.Timer(86400, self._deactivate_poll).start()
        
    def _deactivate_poll(self):
        self.active = False

class Voter():
    def __init__(self, id):
        self.id: int = id
        # randomized dict mapping an alphanumeric letter to a Candidate
        self.options: dict[str, Candidate] = {}
        # ordered list of candidates post-vote
        self.ballot: list[Candidate] = []

def create_poll(entries_str: str) -> int:
    """Parses candidates of poll and returns poll_id."""
    entries_split = entries_str.split(',')
    
    id = create_poll_id()
    print("could not find an id that is not already in use")
    if id == -1:
        return id

    poll = Poll(id)
    for entry in entries_split:
        entry = entry.strip()
        candidate = Candidate(entry)
        poll.candidates.append(candidate)

    print(f"successfully created poll with id: {id}")
    poll_hub[id] = poll
    return id


def get_candidates(poll_id) -> list[Candidate]|None:
    """Return a poll's list of candidates"""
    if poll_id not in poll_hub:
        return None
    return poll_hub[poll_id].candidates


def close_poll(id: int):
    """Close a poll if it exists, removing it permanently from the poll hub. Return poll pesults."""
    print(f"closing poll {id}")
    if id not in poll_hub:
        print(f"Poll with that ID ({id}) not found.")
        return "Poll with that ID not found."
    poll: Poll = poll_hub[id]
    if not poll.active:
        print("Poll has already been closed.")
        return "Poll has already been closed."
    
    candidates = poll.candidates
    ballots = collect_ballots(poll)
    if len(ballots) == 0:
        poll.active = False
        print("No votes for this poll were made! Closing poll")
        return "No votes for this poll were made! Closing poll"
    
    election_result = pyrankvote.instant_runoff_voting(candidates, ballots)
    del poll_hub[id]
    return election_result
    

def create_poll_id() -> int:
    """Creates a unique 4-digit id for the latest poll."""
    id = random.randrange(1000,9999)
    counter = 0
    while id in poll_hub and counter < 100:
        counter += 1
        id = random.randrange(1000,9999)
        
    if counter == 100:
        return -1
    return id

    
def create_ballot(poll_id: int, user_id: int) -> dict[str, Candidate]|None:
    """Randomizes options and creates ballot structure for a particular user."""
    print(f"creating ballot for poll id {poll_id} and user id {user_id}")
    poll: Poll = poll_hub[poll_id]
    
    if not poll.active:
        print(f"poll {poll_id} inactive")
        return None
    
    randomized_candidates = random.sample(poll.candidates, len(poll.candidates))
    voter = Voter(user_id)
    
    for i in range(len(randomized_candidates)):
        option = string.ascii_lowercase[i]
        voter.options[option] = randomized_candidates[i]
    
    poll.voters[user_id] = voter
    return voter.options

def record_vote(poll_id: int, user_id: int, vote_str: str) -> bool|None:
    """Create Ballot list based off user votes, 
    appending candidates randomly to the bottom of the ballot if needed."""
    # TODO: determine mutability of the underlying dicts
    print(f"recording a vote for poll id {poll_id} and user id {user_id}")
    poll: Poll = poll_hub[poll_id]
    if not poll.active:
        print(f"poll {poll_id} inactive")
        return None

    voter: Voter = poll.voters[user_id]
    if len(voter.ballot) != 0:
        print(f"user {user_id} has already voted")
        return None
    
    votes = vote_str.split(',')
    user_options = voter.options.copy()
    ranked_candidates = []
    for vote in votes:
        vote = vote.strip().lower()
        if vote not in user_options:
            if vote in voter.options:
                print(f"user {user_id} has put in a duplicate vote option: {vote}")
                continue
            print(f"user {user_id} has put in at least one invalid vote option: {vote}")
            return False
        item = user_options[vote]
        ranked_candidates.append(item)
        del user_options[vote]
    
    # randomize and append any values not voted for 
    leftovers = list(user_options.values())
    if len(leftovers) != 0:
        if len(leftovers) != 1:
            leftovers = random.sample(leftovers, len(leftovers))
        ranked_candidates.extend(leftovers)    

    voter.ballot = ranked_candidates
    poll.voters[user_id] = voter
    return True
    
def collect_ballots(poll: Poll) -> list[Ballot]:
    """Gather all votes for the poll into a list."""
    ballots = []
    for voter in poll.voters.values():
        ballots.append(Ballot(voter.ballot))
        
    return ballots

def get_user_ballot(poll_id: int, user_id: int):
    """Get pretty-printed ballot for a particular user."""
    if poll_id not in poll_hub:
        print(f"Poll with that ID ({poll_id}) not found.")
        return "Poll with that ID not found."
    poll: Poll = poll_hub[poll_id]
    if not poll.active:
        print("Poll has already been closed.")
        return "Poll has already been closed."
    
    user_ballot: list[Candidate] = poll.voters[user_id].ballot
    ballot_str = ''
    for i in range(len(user_ballot)):
        ballot_str += f"{i+1}  |  {user_ballot[i]}\n"
    
    return ballot_str
    