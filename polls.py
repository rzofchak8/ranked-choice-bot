import random
import string
import pyrankvote
import threading
import time
from pyrankvote import Candidate, Ballot
poll_hub = {}

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

def create_poll(entries_str: str):
    """Parses candidates of poll and returns poll_id."""
    entries_split = entries_str.split(',')
    
    id = create_poll_id()
    
    if id == -1:
        return id

    poll = Poll(id)
    for entry in entries_split:
        entry = entry.strip()
        candidate = Candidate(entry)
        poll.candidates.append(candidate)

    poll_hub[id] = poll
    return id

def close_poll(id: int):
    """Close a poll if it exists, removing it permanently from the poll hub. Return poll pesults."""
    # TODO: collect votes and create ballots
    poll: Poll = poll_hub[id]
    
    candidates = poll.candidates
    ballots = collect_ballots(poll)
    if len(ballots) == 0:
        # TODO: no votes! close poll
        poll.active = False
        return None
        
    election_result = pyrankvote.instant_runoff_voting(candidates, ballots)

    if id in poll_hub:
        del poll_hub[id]
        return election_result
    return None
    
def create_poll_id():
    """Creates a unique 4-digit id for the latest poll."""
    id = random.randrange(1000,9999)
    counter = 0
    while id in poll_hub and counter < 100:
        counter += 1
        id = random.randrange(1000,9999)
        
    if counter == 100:
        return -1
    return id

    
def create_ballot(poll_id: int, user_id: int):
    """Randomizes options and creates ballot structure for a particular user."""
    poll: Poll = poll_hub[poll_id]
    
    if not poll.active:
        # TODO: customized message saying this poll is inactive
        return None
    
    randomized_candidates = random.sample(poll.candidates, len(poll.candidates))
    voter = Voter(user_id)
    
    for i in range(len(randomized_candidates)):
        option = string.ascii_lowercase[i]
        voter.options[option] = randomized_candidates[i]
    
    poll.voters[user_id] = voter
    return voter.options

def record_vote(poll_id: int, user_id: int, vote_str: str):
    """Create Ballot list based off user votes, 
    appending candidates randomly to the bottom of the ballot if needed."""
    # TODO: determine mutability of the underlying dicts
    poll: Poll = poll_hub[poll_id]
    if not poll.active:
        # TODO: customized message saying this poll is inactive
        return None

    voter: Voter = poll.voters[user_id]
    if len(voter.ballot) != 0:
        # TODO: customized message saying you have already voted
        return None
    
    votes = vote_str.split(',')
    user_options = voter.options.copy()
    ranked_candidates = []
    for vote in votes:
        if vote not in user_options:
            # TODO: user error, should they be able to try again?
            return False
        item = user_options[vote]
        ranked_candidates.append(item)
        del user_options[vote]
    
    # randomize and append any values not voted for 
    leftovers = user_options.values()
    if len(leftovers) != 0:
        leftovers = random.sample(leftovers, len(leftovers))
        ranked_candidates.extend(leftovers)    

    voter.ballot = Ballot(ranked_candidates)
    poll.voters[user_id] = voter
    return True
    
def collect_ballots(poll: Poll) -> list[Ballot]:
    """Gather all votes for the poll into a list."""
    ballots = []
    for voter in poll.voters.items():
        voter: Voter
        ballots.append(voter.ballot)
        
    return ballots