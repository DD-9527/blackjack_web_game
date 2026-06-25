import random
from playcard import make_deck, get_suit, get_rank_ace_high, SUITS, get_suit_name
#from userlog import # add_log_entry


def new_game(session):
    session_id = session.get('session_id', '')

    ...

    players = ...

    # Deal 13 cards to each player
    hands = ...

    ## add_log_entry(session_id, f"New Whist game started. Trump is {trump_suit}.")

    # Sort hands for nicer display (optional)
    ...

    session['game_state'] = {
        'players': players,
        'hands': hands,
        'trump_suit': ...,
        'trump_suit_name': ...,
        'stop_type': 'new_trick',
        'leader': 'north',  # or whoever starts
        'tricks': [],  # list of tricks
        'scores': {'south_north': 0, 'east_west': 0},
        'message': None,
        'message_class': "info-message",
    }

    # Flask automatically marks the session as modified when you assign
    # a value to a session key. No need for `session.modified = True`.


def game_update(session, action):
    game_state = session.get('game_state')
    if not game_state:
        return new_game(session)

    session_id = session.get('session_id', '')
    ...