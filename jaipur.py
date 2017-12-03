import enum
import random

from attr import attrs, attrib, validators, Factory
from automat import MethodicalMachine
from multiset import Multiset


# slots=True throughout?

@attrs
class Player:
    # Player attributes
    name = attrib()
    # Hand attributes
    hand = attrib(default=Factory(Multiset))
    # leather = attrib(default=0)
    # spices = attrib(default=0)
    # cloth = attrib(default=0)
    # silver = attrib(default=0)
    # gold = attrib(default=0)
    # diamonds = attrib(default=0)
    # Game attributes
    tokens = list()
    seals = attrib(default=0)

    @property
    def cards_in_hand(self):
        # Camels are not technically in your hand and don't count against the hand limit.
        return len([card for card in self.hand if card.type != CardType.CAMEL])

    @property
    def points(self):
        # TODO: figure out if you can see your own bonus tokens
        return sum([t.value for t in self.tokens])


# TODO: better __repr__?
class CardType(enum.Enum):
    CAMEL = "Camel"
    LEATHER = "Leather"
    SPICE = "Spice"
    CLOTH = "Cloth"
    SILVER = "Silver"
    GOLD = "Gold"
    DIAMONDS = "Diamonds"


# frozen=True
@attrs(hash=True)
class Card:
    type = attrib(validator=validators.in_(CardType))


# frozen=True
@attrs
class Token:
    type = attrib(validator=validators.in_(CardType))
    value = attrib(default=1)


class TokenPile(list):
    def __init__(self, card_type):
        point_map = {
            CardType.LEATHER: [4, 3, 2, 1, 1, 1, 1, 1, 1],
            CardType.SPICE: [5, 3, 3, 2, 2, 1, 1],
            CardType.CLOTH: [5, 3, 3, 2, 2, 1, 1],
            CardType.SILVER: [5, 5, 5, 5, 5],
            CardType.GOLD: [6, 6, 5, 5, 5],
            CardType.DIAMONDS: [7, 7, 5, 5, 5],
        }
        values = point_map[card_type]
        super().__init__(Token(type=card_type, value=val) for val in values)


class Tokens(dict):
    def __init__(self):
        iterable = ((card_type, TokenPile(card_type)) for card_type in CardType if card_type != CardType.CAMEL)
        super().__init__(iterable)


# frozen=True
@attrs
class BonusToken:
    bonus_type = attrib(validator=validators.in_([3,4,5]))
    value = attrib(default=1)


class ShuffleableObject(list):
    def shuffle(self):
        # Shuffle the list in-place.
        random.shuffle(self)


class BonusTokenPile(ShuffleableObject):
    def __init__(self, bonus_type):
        if bonus_type == 3:
            values = [1, 1, 2, 2, 2, 3, 3]
        elif bonus_type == 4:
            values = [4, 4, 5, 5, 6, 6]
        elif bonus_type == 5:
            values = [8, 8, 9, 10, 10]
        else:
            raise ValueError
        tokens = [BonusToken(bonus_type=bonus_type, value=val) for val in values]
        super().__init__(tokens)


class Bonuses(dict):
    def __init__(self):
        iterable = ((bonus_type, BonusTokenPile(bonus_type)) for bonus_type in [3, 4, 5])
        super().__init__(iterable)


class Deck(ShuffleableObject):
    pass


class StandardDeck(Deck):
    def __init__(self):
        cards = {
            CardType.CAMEL: 11,
            CardType.LEATHER: 10,
            CardType.SPICE: 8,
            CardType.CLOTH: 8,
            CardType.SILVER: 6,
            CardType.GOLD: 6,
            CardType.DIAMONDS: 6,
        }
        args = [Card(type=k) for k, v in cards.items() for _ in range(v)]
        super().__init__(args)


class PlayArea(Multiset):
    pass


class ActionType(enum.Enum):
    TAKE_MANY = "Exchange"
    TAKE_SINGLE = "Take One Good"
    TAKE_CAMELS = "Take All Camels"
    SELL = "Sell Cards"


@attrs
class JaipurGame:
    player1 = attrib(default=Factory(lambda: Player(name='Player 1')))
    player2 = attrib(default=Factory(lambda: Player(name='Player 2')))
    play_area = attrib(default=Factory(PlayArea))
    deck = attrib(default=Factory(StandardDeck))
    tokens = attrib(default=Factory(Tokens))
    bonuses = attrib(default=Factory(Bonuses))

    machine = MethodicalMachine()

    # def fill_play_area(self):
    #     pass

    @machine.state(initial=True)
    def setup(self):
        "The game is being set up."

    @machine.state()
    def player1_turn(self):
        "Player 1 should select an action."

    @machine.state()
    def player2_turn(self):
        "Player 2 should select an action."

    @machine.input()
    def start(self):
        pass

    @machine.output()
    def setup_game(self):
        # Shuffle the deck.
        self.deck.shuffle()

        # Shuffle each bonus token pile.
        [pile.shuffle() for pile in self.bonuses.values()]

        # Deal 3 camels to the play area.
        for _ in range(3):
            i = self.deck.index(Card(type=CardType.CAMEL))
            camel = self.deck.pop(i)
            self.play_area.add(camel)

        # Deal 2 other cards.
        for _ in range(2):
            top_card = self.deck.pop()
            self.play_area.add(top_card)

        # Deal 5 cards to each player.
        for _ in range(5):
            top_card = self.deck.pop()
            self.player1.hand.add(top_card)
        for _ in range(5):
            top_card = self.deck.pop()
            self.player2.hand.add(top_card)

    @machine.input()
    def player1_action(self, action_type, **kwargs):
        "Player 1 took an action."

    @machine.input()
    def player2_action(self, action_type, **kwargs):
        "Player 2 took an action."

    @machine.output()
    def take_player1_action(self, action_type, **kwargs):
        self.take_action('player1', action_type, **kwargs)

    @machine.output()
    def take_player2_action(self, action_type, **kwargs):
        self.take_action('player2', action_type, **kwargs)

    def take_action(self, player_attr, action_type, **kwargs):
        player = getattr(self, player_attr)
        if action_type == ActionType.TAKE_CAMELS:
            self.play_area.get()


    setup.upon(start, enter=player1_turn, outputs=[setup_game])
    # TODO: check for victory/end conditions, execute action
    player1_turn.upon(player1_action, enter=player2_turn, outputs=[take_player1_action])
    player2_turn.upon(player2_action, enter=player1_turn, outputs=[take_player2_action])

    # actions

    # take

    # sell
    # types
