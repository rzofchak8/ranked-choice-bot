import random
import string
import pyrankvote
from pyrankvote import Candidate, Ballot
poll_hub = {}

# class Poll() {
#     def __init__(self)
# }

def create_poll(entries_str: str):
    """Parses candidates of poll and returns poll_id."""
    entries_split = entries_str.split(',')
    
    id = create_poll_id()
    
    if id == -1:
        return id

    #FIXME make into its own class
    poll = {}
    poll['active'] = True
    
    candidates = []
    for entry in entries_split:
        entry = entry.strip()
        candidate = Candidate(entry)
        candidates.append(candidate)
        msg += f'- {entry}\n'
            
    poll['candidates'] = candidates
    poll['voters'] = {}
    
    poll_hub[id] = poll
    return id

def close_poll(id: int):
    """Close a poll if it exists, removing it permanently from the poll hub. Return poll pesults."""
    # TODO: collect votes and create ballots
    
    
    candidates = poll_hub['candidates']
    ballots = poll_hub['ballots']
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

def collect_ballots(id):
    votes = poll_hub[id]['votes']
    
def create_ballot(poll_id: int, user_id: int):
    poll = poll_hub[poll_id]
    
    randomized_candidates = random.sample(poll['candidates'], len(poll['candidates']))
    
    user_options = {}
    
    for i in range(len(randomized_candidates)):
        option = string.ascii_lowercase[i]
        user_options[option] = randomized_candidates[i]
    
    poll['voters'][user_id] = {
        'options': user_options,
        'vote': '',
    }
    return user_options

def record_vote(poll_id: int, user_id: int, vote_str: str):
    # TODO: determine mutability of the underlying dicts
    poll = poll_hub[poll_id]
    votes = vote_str.split(',')
    user_options = poll['voters'][user_id]['options']
    user_ballot = []
    for vote in votes:
        if vote not in user_options:
            # TODO: user error, should they be able to try again?
            return False
        item = user_optionsr
        user_ballot.append(user_options[vote])
    

    poll['voters'][user_id]['ballot'] = user_ballot