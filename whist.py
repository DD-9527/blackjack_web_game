import random
from playcard import make_deck, get_suit, get_rank_ace_high, SUITS, get_suit_name

# from userlog import add_log_entry

# Clockwise play order on the table: North -> East -> South -> West -> North
ORDER = ['north', 'east', 'south', 'west']

# Team assignments
TEAM = {
    'north': 'south_north',
    'south': 'south_north',
    'east': 'east_west',
    'west': 'east_west',
}


def next_player(current: str) -> str:
    """Return the next player in clockwise order."""
    return ORDER[(ORDER.index(current) + 1) % 4]


def sort_hand(hand):
    """Sort a hand by suit (S, H, D, C) then by rank (Ace-high)."""
    return sorted(hand, key=lambda c: (SUITS.index(c[1]), get_rank_ace_high(c)))


def get_legal_plays(hand, trick, leader, trump_suit):
    """Return the list of legally playable cards for a player."""
    if not trick:
        # Leading: any card is allowed
        return list(hand)

    lead_suit = trick[leader][1]
    same_suit = [c for c in hand if c[1] == lead_suit]
    if same_suit:
        return same_suit
    else:
        # Void in lead suit: can play any card (including trump)
        return list(hand)


def ai_play_random(hand, trick, leader, trump_suit):
    """AI chooses a random legal card to play."""
    legal = get_legal_plays(hand, trick, leader, trump_suit)
    return random.choice(legal)


def get_trick_winner(trick, leader, trump_suit):
    """Determine which player wins the current trick."""
    lead_suit = trick[leader][1]

    # Check for trump cards
    trump_plays = {p: c for p, c in trick.items() if c[1] == trump_suit}
    if trump_plays:
        winner = max(trump_plays, key=lambda p: get_rank_ace_high(trump_plays[p]))
        return winner

    # Otherwise highest card of the lead suit wins
    lead_plays = {p: c for p, c in trick.items() if c[1] == lead_suit}
    winner = max(lead_plays, key=lambda p: get_rank_ace_high(lead_plays[p]))
    return winner


def new_game(session):
    """Initialize a new Whist game."""
    session_id = session.get('session_id', '')
    deck = make_deck()
    random.shuffle(deck)

    # Deal 13 cards to each player (one by one, like real Whist)
    hands = {'north': [], 'south': [], 'east': [], 'west': []}
    for i, card in enumerate(deck):
        player = ORDER[i % 4]
        hands[player].append(card)

    # Sort each hand for nicer display
    for player in hands:
        hands[player] = sort_hand(hands[player])

    # Randomly determine trump suit
    trump_suit = random.choice(SUITS)

    # First leader is the player to the left of the dealer
    # Since we deal in ORDER starting from north, the last card goes to west,
    # so the dealer (who dealt last) is west, and the first leader is north.
    # But to make it simple, just start with north as leader.
    leader = 'north'

    # add_log_entry(session_id,
    #               f"New Whist game started. Trump is {get_suit_name(trump_suit)}.")

    session['game_state'] = {
        'players': {
            'north': 'North',
            'south': 'You',
            'east': 'East',
            'west': 'West',
        },
        'hands': hands,
        'trump_suit': trump_suit,
        'trump_suit_name': get_suit_name(trump_suit),
        'stop_type': 'new_trick',
        'leader': leader,
        'tricks': [{}],  # First element is the current (empty) trick
        'scores': {'south_north': 0, 'east_west': 0},
        'message': f'Trump suit: {get_suit_name(trump_suit)}.',
        'message_class': 'info-message',
    }
    # Flask automatically marks the session as modified when you assign
    # a value to a session key. No need for `session.modified = True`.


def game_update(session, action):
    """Process a game action from the player."""
    game_state = session.get('game_state')
    if not game_state:
        return new_game(session)

    # session_id = session.get('session_id', '')

    if action == 'new_trick':
        _handle_new_trick(game_state)
    elif action.startswith('play/'):
        card = action[5:]  # e.g. 'play/AS' -> 'AS'
        _handle_play(game_state, card)
    # else: unknown action, ignore

    session.modified = True


def _handle_new_trick(game_state):
    """
    Player clicked 'New Trick'.
    If a previous trick was just completed (trick_done), first create a
    fresh empty trick. Then let AI players play until it's South's turn
    or until the trick is complete.
    """
    # If the previous trick was completed and kept visible, now create
    # a new empty trick for the next round.
    if game_state['stop_type'] == 'trick_done':
        game_state['tricks'].append({})

    trick = game_state['tricks'][-1]
    hands = game_state['hands']
    leader = game_state['leader']
    trump_suit = game_state['trump_suit']

    while True:
        # Determine whose turn it is
        if not trick:
            next_p = leader
        else:
            last = list(trick.keys())[-1]
            next_p = next_player(last)

        # If it's South's turn, stop and wait for user input
        if next_p == 'south':
            if not trick:
                game_state['stop_type'] = 'lead_card'
                game_state['message'] = 'Your turn to lead.'
                game_state['message_class'] = 'info-message'
            else:
                game_state['stop_type'] = 'follow_card'
                game_state['message'] = 'Your turn to follow.'
                game_state['message_class'] = 'info-message'
            return

        # AI plays
        card = ai_play_random(hands[next_p], trick, leader, trump_suit)
        trick[next_p] = card
        hands[next_p].remove(card)
        # add_log_entry(session_id, f'{next_p.capitalize()} plays {card}.')

        if len(trick) == 4:
            # All four players have played — resolve the trick
            _resolve_trick(game_state)
            return


def _handle_play(game_state, card):
    """
    South has played a card (via `play/<card>`).
    Record the card, then let remaining AI players play,
    and finally resolve the trick.
    """
    trick = game_state['tricks'][-1]
    hands = game_state['hands']
    leader = game_state['leader']
    trump_suit = game_state['trump_suit']

    # Validate: card must be in South's hand
    if card not in hands['south']:
        return

    # South plays
    trick['south'] = card
    hands['south'].remove(card)
    # add_log_entry(session_id, f'South plays {card}.')

    # Let remaining AI players (after South) play
    while len(trick) < 4:
        last = list(trick.keys())[-1]
        next_p = next_player(last)

        # Safety check — should always be an AI
        if next_p == 'south':
            break

        ai_card = ai_play_random(hands[next_p], trick, leader, trump_suit)
        trick[next_p] = ai_card
        hands[next_p].remove(ai_card)
        # add_log_entry(session_id, f'{next_p.capitalize()} plays {ai_card}.')

    if len(trick) == 4:
        _resolve_trick(game_state)


def _resolve_trick(game_state):
    """Determine trick winner, update scores, and keep trick visible.
    The completed trick remains in `tricks[-1]` so the cards stay on screen.
    Only when the user clicks 'New Trick' will a new empty trick be created."""
    trick = game_state['tricks'][-1]
    leader = game_state['leader']
    trump_suit = game_state['trump_suit']

    winner = get_trick_winner(trick, leader, trump_suit)
    winning_team = TEAM[winner]
    game_state['scores'][winning_team] += 1
    # --- DEBUG LOG ---
    with open('whist_debug.log', 'a') as f:
        f.write(f"TRICK: {trick}\n")
        f.write(f"  leader={leader}, trump={trump_suit}\n")
        f.write(f"  winner={winner}, team={winning_team}\n")
        f.write(f"  scores: SN={game_state['scores']['south_north']}, EW={game_state['scores']['east_west']}\n")
    # --- DEBUG LOG END ---

    total_tricks = sum(game_state['scores'].values())
    # add_log_entry(session_id,
    #               f'{winner.capitalize()} wins the trick for team {winning_team}. '
    #               f'Score: SN={game_state["scores"]["south_north"]}, '
    #               f'EW={game_state["scores"]["east_west"]}.')

    if total_tricks >= 13:
        # Game over — keep last trick visible, show final message
        game_state['stop_type'] = 'game_over'
        sn = game_state['scores']['south_north']
        ew = game_state['scores']['east_west']
        if sn > ew:
            game_state['message'] = f'You Win! South-North: {sn}, East-West: {ew}'
            game_state['message_class'] = 'win-message'
        elif ew > sn:
            game_state['message'] = f'You Lose! South-North: {sn}, East-West: {ew}'
            game_state['message_class'] = 'lose-message'
        else:
            game_state['message'] = f"It's a tie! South-North: {sn}, East-West: {ew}"
            game_state['message_class'] = 'tie-message'
        # add_log_entry(session_id, f'Game over. Final score: SN={sn}, EW={ew}.')
    else:
        # Keep the completed trick visible — do NOT append {} yet.
        # User must click "New Trick" to proceed.
        game_state['leader'] = winner
        game_state['stop_type'] = 'trick_done'
        game_state['message'] = f'{winner.capitalize()} wins the trick!'
        game_state['message_class'] = 'info-message'
