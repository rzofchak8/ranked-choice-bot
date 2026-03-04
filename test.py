import random

hub = {}

def create_poll_id():
    poll_id = random.randrange(1000,9999)
    counter = 0
    while poll_id in hub and counter < 10:
        counter += 1
        poll_id = random.randrange(1000,9999)
        
    print(poll_id)
    print(counter)
    
create_poll_id()