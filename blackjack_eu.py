import random
from playcard import make_deck
#from userlog import add_log_entry

CARD_VALUES = {
    'A': 11,
    '2': 2,
    '3': 3,
    '4': 4,
    '5': 5,
    '6': 6,
    '7': 7,
    '8': 8,
    '9': 9,
    'T': 10,
    'J': 10,
    'Q': 10,
    'K': 10,
}


def calculate_hand_value(hand):
    # Calculate the value of a hand, considering Aces as 1 or 11.
    value, aces = 0, 0
    for card in hand:
        rank = card[0]
        value += CARD_VALUES[rank]
        aces += rank == 'A'

    # Adjust for Aces if needed
    while value > 21 and aces:
        value -= 10
        aces -= 1

    return value


def new_game(session):
    # European Blackjack: Dealer gets only 1 card initially, no hole card.
    session_id = session.get('session_id', '')
    deck = make_deck()
    random.shuffle(deck)
    # Deal: card1 & card3 go to player, card2 goes to dealer (only 1 card)
    card1, card2, card3 = deck.pop(), deck.pop(), deck.pop()
    player_hand = [card1, card3]
    dealer_hand = [card2]          # Dealer starts with just 1 card (no hole card)
    dealer_value = calculate_hand_value(dealer_hand)
    player_value = calculate_hand_value(player_hand)
    # Track whether player's first two cards form a natural blackjack
    player_has_natural = (len(player_hand) == 2 and player_value == 21)

    # No initial blackjack check for dealer (only 1 card, impossible)
    session['game_state'] = {
        'deck': deck,
        'dealer_hand': dealer_hand,
        'player_hand': player_hand,
        'dealer_value': dealer_value,
        'player_value': player_value,
        'player_has_natural': player_has_natural,
        'message': None,
        'message_class': "",
    }
    # Flask automatically marks the session as modified when you assign
    # a value to a session key. No need for `session.modified = True`.


def game_update(session, action):
    game_state = session.get('game_state', {})
    if not game_state:
        return new_game(session)

    session_id = session.get('session_id', '')
    deck = game_state['deck']
    dealer_hand = game_state['dealer_hand']
    player_hand = game_state['player_hand']
    player_has_natural = game_state.get('player_has_natural', False)

    if action == 'hit':
        # Deal a card to the player
        card = deck.pop()
        player_hand.append(card)
        player_value = calculate_hand_value(player_hand)
        game_state['player_value'] = player_value
        #add_log_entry(session_id, f'Player hits and gets {card}.')

        # Check if player busts
        if player_value > 21:
            game_state['dealer_value'] = calculate_hand_value(dealer_hand)
            game_state['message'] = 'You busted! Dealer wins.'
            game_state['message_class'] = 'lose-message'
            #add_log_entry(session_id, 'Player busts and loses.')
    elif action == 'stand':
        # Player stands first. Now dealer draws the second card (hole card).
        player_value = game_state['player_value']
        card = deck.pop()
        dealer_hand.append(card)
        dealer_value = calculate_hand_value(dealer_hand)

        # Check for dealer's natural blackjack (first two cards = 21)
        if dealer_value == 21 and len(dealer_hand) == 2:
            game_state['dealer_value'] = dealer_value
            if player_has_natural:
                # Both have natural blackjack → tie
                game_state['message'] = "It's a tie of double blackjack!"
                game_state['message_class'] = 'tie-message'
            else:
                # Dealer natural blackjack beats any non-natural player hand
                game_state['message'] = 'Dealer wins with a natural blackjack!'
                game_state['message_class'] = 'lose-message'
        else:
            # No dealer natural blackjack → dealer draws to 17 normally
            while dealer_value < 17:
                card = deck.pop()
                dealer_hand.append(card)
                dealer_value = calculate_hand_value(dealer_hand)

            game_state['dealer_value'] = dealer_value

            # Determine the winner
            if dealer_value > 21:
                game_state['message'] = 'Dealer busted! You win!'
                game_state['message_class'] = 'win-message'
            elif dealer_value > player_value:
                game_state['message'] = 'Dealer wins!'
                game_state['message_class'] = 'lose-message'
            elif dealer_value < player_value:
                game_state['message'] = 'You win!'
                game_state['message_class'] = 'win-message'
            else:
                game_state['message'] = "It's a tie!"
                game_state['message_class'] = 'tie-message'
    else:
        # add_log_entry(session_id, f'Unknown action {action}.')
        return

    # game state has changed itself so tell session it has changed
    session.modified = True
