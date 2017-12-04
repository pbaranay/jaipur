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
    tokens = attrib(default=Factory(list))
    seals = attrib(default=0)

    @property
    def cards_in_hand(self):
        # Camels are not technically in your hand and don't count against the hand limit.
        return sum(self.hand[card_type] for card_type in CardType if card_type != CardType.CAMEL)

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
        args = [card_type for card_type, num in cards.items() for _ in range(num)]
        super().__init__(args)


class PlayArea(Multiset):
    pass


class ActionType(enum.Enum):
    TAKE_MANY = "Exchange"
    TAKE_SINGLE = "Take One Good"
    TAKE_CAMELS = "Take All Camels"
    SELL = "Sell Cards"


class IllegalPlayError(Exception):
    """A player tried to take an illegal action."""


@attrs
class JaipurGame:
    player1 = attrib(default=Factory(lambda: Player(name='Player 1')))
    player2 = attrib(default=Factory(lambda: Player(name='Player 2')))
    play_area = attrib(default=Factory(PlayArea))
    deck = attrib(default=Factory(StandardDeck))
    tokens = attrib(default=Factory(Tokens))
    bonuses = attrib(default=Factory(Bonuses))
    current_player = attrib(default=Factory(lambda self: self.player1, takes_self=True))

    PRECIOUS_GOODS = [CardType.SILVER, CardType.GOLD, CardType.DIAMONDS]

    machine = MethodicalMachine()

    # def fill_play_area(self):
    #     pass

    @machine.state(initial=True)
    def setup(self):
        "The game is being set up."

    @machine.state()
    def player_turn(self):
        "A player should select an action."

    @machine.state()
    def between_turns(self):
        "The game is in between turns."

    @machine.state()
    def player1_victory(self):
        "Player 1 wins!"

    @machine.state()
    def player2_victory(self):
        "Player 2 wins!"

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
            i = self.deck.index(CardType.CAMEL)
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
    def player_action(self, action_type, *args):
        "A player took an action."

    @machine.output()
    def take_action(self, action_type, *args):
        player = self.current_player
        if action_type == ActionType.TAKE_CAMELS:
            num_camels = self.play_area[CardType.CAMEL]
            if not num_camels:
                raise IllegalPlayError("There are no camels to take.")
            self.play_area[CardType.CAMEL] = 0
            player.hand[CardType.CAMEL] += num_camels
        elif action_type == ActionType.TAKE_SINGLE:
            card_type_to_take = args[0]
            if card_type_to_take in self.play_area:
                self.play_area[card_type_to_take] -= 1
                player.hand[card_type_to_take] += 1
            else:
                raise IllegalPlayError("There is no {} to take.".format(card_type_to_take))
        elif action_type == ActionType.TAKE_MANY:
            card_types_to_take, card_types_to_give = Multiset(args[0]), Multiset(args[1])
            if len(card_types_to_take) != len(card_types_to_give):
                raise ValueError
            if len(card_types_to_take) <= 1:
                raise IllegalPlayError("You must exchange at least two cards from your hand and/or herd.")
            # Cannot take camels this way.
            if CardType.CAMEL in card_types_to_take:
                raise IllegalPlayError("You cannot take camels this way.")
            # The same type of good cannot be both taken and surrendered.
            if card_types_to_take.distinct_elements() < card_types_to_give:
                raise IllegalPlayError("You cannot surrender and take the same type of goods.")
            # The exchange must be legal.
            if card_types_to_take > self.play_area:
                raise IllegalPlayError("Some of the cards you want to take are not in the market.")
            if card_types_to_give > player.hand:
                raise IllegalPlayError("Some of the cards you want to surrender are not in your hand and/or herd.")
            # Exchange the cards.
            self.play_area -= card_types_to_take
            self.play_area += card_types_to_give
            player.hand -= card_types_to_give
            player.hand += card_types_to_take
        elif action_type == ActionType.SELL:
            card_type_to_sell, quantity_to_sell = args[0], args[1]
            if card_type_to_sell == CardType.CAMEL:
                raise IllegalPlayError("You cannot sell camels.")
            if quantity_to_sell == 0:
                raise IllegalPlayError("You cannot sell zero cards.")
            num_card = player.hand[card_type_to_sell]
            if num_card < quantity_to_sell:
                raise IllegalPlayError("You cannot sell {} {} cards; you only have {}.".format(
                    quantity_to_sell,
                    card_type_to_sell,
                    num_card))
            if card_type_to_sell in self.PRECIOUS_GOODS and quantity_to_sell == 1:
                raise IllegalPlayError("You cannot sell a single {}.".format(card_type_to_sell))
            # Execute the sale in three parts.
            # 1) Remove cards from hand.
            player.hand[card_type_to_sell] -= quantity_to_sell
            # 2) Award goods tokens.
            for _ in quantity_to_sell:
                try:
                    player.tokens.append(self.tokens[card_type_to_sell].pop())
                except IndexError:
                    # Sometimes the goods tokens are all gone; the seller simply doesn't get one.
                    pass
            # 3) Award bonus token, if applicable.
            bonus_quantity = min(quantity_to_sell, 5)
            if bonus_quantity in self.bonuses:
                try:
                    player.tokens.append(self.bonuses[bonus_quantity].pop())
                except IndexError:
                    # The rulebook doesn't account for the scenario where all the bonus tokens are gone, but by
                    # extension with the above rule we can presume that the seller simply doesn't get one.
                    pass
        else:
            raise ValueError("You have chosen an unrecognized action.")
        # Fill play area.
        while len(self.play_area) < 5:
            top_card = self.deck.pop()
            self.play_area.add(top_card)
            # TODO: Handle empty deck.
        # Toggle the current player.
        if player == self.player1:
            self.current_player = self.player2
        elif player == self.player2:
            self.current_player = self.player1

    @machine.input()
    def next_turn(self):
        "Advance to the next turn."

    @machine.input()
    def player1_earns_seal(self):
        "Player 1 wins a seal."

    @machine.input()
    def player2_earns_seal(self):
        "Player 2 wins a seal."

    @machine.input()
    def player1_wins(self):
        "Player 1 wins the game."

    @machine.input()
    def player2_wins(self):
        "Player 2 wins the game."

    setup.upon(start, enter=player_turn, outputs=[setup_game])
    # TODO: check for victory/end conditions, execute action
    player_turn.upon(player_action, enter=between_turns, outputs=[take_action])
    between_turns.upon(next_turn, enter=player_turn)
    between_turns.upon(player1_earns_seal, enter=setup)
    between_turns.upon(player2_earns_seal, enter=setup)
    between_turns.upon(player1_wins, enter=player1_victory)
    between_turns.upon(player2_wins, enter=player2_victory)

    # actions

    # take

    # sell
    # types
