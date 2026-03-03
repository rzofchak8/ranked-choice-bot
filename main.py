import pyrankvote
from pyrankvote import Candidate, Ballot


# input csv list of candidates on action /poll_create, create candidate list
# and return a list of options, an id and a button to request a ballot 
# user click should receive a dm with alphabetical kvps to options (randomized)
# dm input csv list of options mapped to user options
# for each unique user, create a ballot and add to list

# /poll_close w/ id, run instant_cutoff_voting, return message with results

bush = Candidate("George W. Bush (Republican)")
gore = Candidate("Al Gore (Democratic)")
nader = Candidate("Ralph Nader (Green)")

candidates = [bush, gore, nader]

# Bush have most first choice votes, but because Ralph Nader-voters want
# Al Gore if Nader is not elected, the elected candidate is Al Gore
ballots = [
    Ballot(ranked_candidates=[bush, nader, gore]),
    Ballot(ranked_candidates=[bush, nader, gore]),
    Ballot(ranked_candidates=[bush, nader]),
    Ballot(ranked_candidates=[bush, nader]),
    Ballot(ranked_candidates=[nader, gore, bush]),
    Ballot(ranked_candidates=[nader, gore]),
    Ballot(ranked_candidates=[gore, nader, bush]),
    Ballot(ranked_candidates=[gore, nader]),
    Ballot(ranked_candidates=[gore, nader])
]

# You can use your own Candidate and Ballot objects as long as they implement the same properties and methods
election_result = pyrankvote.instant_runoff_voting(candidates, ballots)

winners = election_result.get_winners()
# Returns: [<Candidate('Al Gore (Democratic)')>]

print(election_result)
# Prints:
"""
ROUND 1
Candidate                      Votes  Status
---------------------------  -------  --------
George W. Bush (Republican)        4  Hopeful
Al Gore (Democratic)               3  Hopeful
Ralph Nader (Green)                2  Rejected

FINAL RESULT
Candidate                      Votes  Status
---------------------------  -------  --------
Al Gore (Democratic)               5  Elected
George W. Bush (Republican)        4  Rejected
Ralph Nader (Green)                0  Rejected
"""