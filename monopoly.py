from random import randint
from collections import defaultdict
from itertools import cycle, combinations
from __builtin__ import False

JAIL_TILE = 10
GOTO_JAIL_TILE = 30

class GoToJailException(Exception):
    pass

class BankruptException(Exception):

    def __init__(self, msg, caused_by):
        super(BankruptException, self).__init__(msg)
        self.caused_by = caused_by

class DeedPrices(object):

    def __init__(self):
        self.deed_cost = {}
        self.house_cost = {}
        self.mortgage = {}
        self.name = defaultdict(str)
        self.rent = defaultdict(lambda: [0] * 6)
        self.color = {}
        self.colors = defaultdict(list)

        with open("monopoly.csv") as f:
            header = f.readline().rstrip().split(",")
            for line in f:
                deed = dict(zip(header, line.rstrip().split(",")))
                tile = int(deed['tile'])

                self.deed_cost[tile] = int(deed['deed_cost'])
                self.house_cost[tile] = int(deed['house_cost'])
                self.mortgage[tile] = int(deed['deed_cost']) / 2
                self.name[tile] = deed['name']

                self.rent[tile] = [int(deed['rent']),
                                   int(deed['house_1']),
                                   int(deed['house_2']),
                                   int(deed['house_3']),
                                   int(deed['house_4']),
                                   int(deed['hotel'])]

                self.color[tile] = deed['color']
                self.colors[deed['color']].append(tile)

    def print_deeds(self, indexes):
        for index, value in enumerate(indexes):
            if value and index in self.color:
                print self.color[index], self.name[index]


class NotSpecial(object):

    def get_price(self, player):
        return 0

class IncomeTax(object):

    def __init__(self, board):
        self.board = board

    def get_price(self, player):
        cash_left = self.board.get_cash_left(player)
        return min(200, cash_left * 0.1)

class LuxuryTax(object):

    def get_price(self, player):
        return 75

class Board(object):

    def __init__(self, players=None):
        if players is None:
            self.players = [Player(), BuyAll(), BuyFrom(10), BuyBetween(10, 20), GaPlayer([0, 0, 1, 0, 1, 1, 0, 0, 1, 0, 0, 1, 1, 1, 1, 1, 1, 0, 1, 1, 0, 0, 0, 0, 0, 1, 0, 1, 0, 0, 1, 1, 0, 1, 0, 1, 1, 1, 0, 1])]
            self.players = [BuyAll(), GaPlayer([0, 1, 0, 1, 0, 1, 1, 0, 0, 1, 0, 1, 0, 1, 1, 1, 1, 0, 1, 1, 0, 0, 0, 1, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0, 1, 0, 1])]
            self.players = [BuyAll(), GaPlayer([0, 1, 0, 1, 0, 1, 1, 0, 1, 1, 0, 1, 0, 1, 1, 1, 1, 0, 1, 1, 0, 0, 0, 1, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 1])]
            self.players = [BuyAll(), GaPlayer([0, 1, 0, 1, 0, 1, 1, 0, 1, 1, 0, 1, 1, 1, 1, 1, 1, 0, 1, 1, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 1])]
        else:
            self.players = players

        for player in self.players:
            player.board = self

        # self.players = [Player(self), BuyAll(self)]
        self.history = defaultdict(list)
        self.position = defaultdict(int)
        self.jail_turns_left = defaultdict(int)
        self.bank = Bank()
        self.prices = DeedPrices()
        self.players_cash = dict((player, 1500) for player in self.players)

        self.deed_owners = [None] * 40
        self.deed_owners[0] = self.bank
        self.deed_owners[10] = self.bank
        self.deed_owners[20] = self.bank
        self.deed_owners[30] = self.bank

        self.deed_owners[2] = self.bank  # community chest
        self.deed_owners[4] = self.bank  # income tax
        self.deed_owners[7] = self.bank  # chance
        self.deed_owners[17] = self.bank  # community chest
        self.deed_owners[22] = self.bank  # chance
        self.deed_owners[33] = self.bank  # community chest
        self.deed_owners[36] = self.bank  # chance
        self.deed_owners[38] = self.bank  # luxury tax

        self.special_deeds = [NotSpecial()] * 40
        self.special_deeds[4] = IncomeTax(self)
        self.special_deeds[38] = LuxuryTax()

        self.is_mortgaged = [False] * 40
        self.houses = [0] * 40

        self.money_raised = [0] * 40
        self.money_invested = [0] * 40
        self.caused_bankruptcy = [0] * 40

    def get_price(self, player, position):
        if self.deed_owners[position] != self.bank:
            color = self.prices.color[position]
            if color == 'rr':
                nr_owned = sum(self.deed_owners[tile] == self.deed_owners[position] for tile in self.prices.colors[color])
                return self.prices.rent[position][nr_owned]

            elif color == 'utility':
                nr_owned = sum(self.deed_owners[tile] == self.deed_owners[position] for tile in self.prices.colors[color])
                d1, d2 = self.dice_roll()
                return self.prices.rent[position][nr_owned] * (d1 + d2)

            else:
                nr_houses = self.houses[position]
                if nr_houses == 0:
                    if all(self.deed_owners[tile] == self.deed_owners[position] for tile in self.prices.colors[color]):
                        # all houses owned by the same player?
                        return self.prices.rent[position][nr_houses] * 2
                return self.prices.rent[position][nr_houses]

        return self.special_deeds[position].get_price(player)

    def dice_roll(self):
        return randint(1, 6), randint(1, 6)

    def get_position(self, player):
        return self.position[player]

    def buy_deed(self, player, tile, amount=None):
        if self.deed_owners[tile] is None:
            if amount is None:
                amount = self.prices.deed_cost[tile]
            cash_left = self.players_cash[player]

            if cash_left >= amount:
                self.deed_owners[tile] = player
                self.players_cash[player] -= amount
                self.money_invested[tile] += amount

                return True
        return False

    def transfer_deed(self, player, other_player, tile):
        assert player == self.deed_owners[tile]

        if self.houses[tile] == 0 and other_player != self.bank:
            # need to pay 10% interest over mortgaged properties
            if self.is_mortgaged[tile]:
                amount = self.prices.deed_cost[tile] * .1
            else:
                amount = 0

            cash_left = self.players_cash[player]
            if cash_left > amount:
                self.deed_owners[tile] = other_player
                self.players_cash[other_player] -= amount
                return True

        return False

    def get_cash_left(self, player):
        return self.players_cash[player]

    def pay_up(self, player, caused_by, amount):
        cash_left = self.players_cash[player]
        if amount > cash_left:
            player.raise_amount(amount - cash_left)

        # check if player succeeded
        cash_left = self.players_cash[player]
        if amount > cash_left:
            raise BankruptException("needed to pay %d, didn't manage only raised %d" % (amount, cash_left), caused_by)

        self.players_cash[player] -= amount

        if caused_by != self.bank:
            self.players_cash[caused_by] += amount

    def get_deeds(self, player):
        return [tile for tile, owner in enumerate(self.deed_owners) if owner == player]

    def get_mortgagable_deeds(self, player):
        return [tile for tile, owner in enumerate(self.deed_owners) if owner == player and not self.is_mortgaged[tile] and self.houses[tile] == 0]

    def add_mortgage(self, player, tile):
        assert player == self.deed_owners[tile]

        if not self.is_mortgaged[tile] and self.houses[tile] == 0:
            self.is_mortgaged[tile] = True
            self.players_cash[player] += self.prices.mortgage[tile]
            return True
        return False

    def sell_mortgage(self, player, tile):
        assert player == self.deed_owners[tile]

        cost = self.prices.mortgage[tile] * 1.1
        if self.players_cash[player] > cost:
            self.is_mortgaged[tile] = False
            self.players_cash[player] -= cost

    def get_morgages_owned(self, player):
        return [tile for tile, owner in enumerate(self.deed_owners) if owner == player and self.is_mortgaged[tile]]

    def get_streets_owned(self, player):
        deeds = self.get_deeds(player)
        colors = set(self.prices.color[tile] for tile in deeds)

        all_owned = []
        for color in colors:
            if all(self.deed_owners[tile] == player for tile in self.prices.colors[color]):
                all_owned.append(color)

        return all_owned

    def add_house(self, player, tile):
        color = self.prices.color[tile]
        if color not in ('rr', 'utility'):  # cannot buy houses for rr and utility
            if all(not self.is_mortgaged[street_tile] for street_tile in self.prices.colors[color]):
                houses_build = self.houses[tile]
                min_houses_build = min(self.houses[street_tile] for street_tile in self.prices.colors[color])

                if houses_build == min_houses_build and houses_build < 5:
                    if houses_build < 4:
                        nr_houses_sold = sum(nr_houses for nr_houses in self.houses if nr_houses < 5)
                        if nr_houses_sold >= 32:
                            return False

                    if houses_build == 4:
                        nr_hotels_sold = sum(nr_houses == 5 for nr_houses in self.houses)
                        if nr_hotels_sold >= 12:
                            return False

                    cost = self.prices.house_cost[tile]
                    if self.players_cash[player] > cost:
                        self.houses[tile] += 1
                        self.players_cash[player] -= cost
                        self.money_invested[tile] += cost
                        return True
        return False

    def sell_house(self, player, tile):
        assert player == self.deed_owners[tile]

        if self.houses[tile] > 0:
            self.houses[tile] -= 1
            self.players_cash[player] += self.prices.house_cost[tile] / 2

    def get_houses(self, player):
        return [(tile, self.houses[tile]) for tile in self.get_deeds(player) if self.houses[tile] > 0]

    def get_house_price(self, color):
        tile = self.prices.colors[color][0]
        return self.prices.house_cost[tile]

    def update_position(self, player, d1, d2):
        old_position = self.position[player]
        new_position = self.position[player] = (old_position + d1 + d2) % 40
        if new_position == GOTO_JAIL_TILE:
            raise GoToJailException()

        self.history[player].append(new_position)

        # passed start
        if old_position > new_position:
            self.players_cash[player] += 200

        # available for purchase?
        deed_owner = self.deed_owners[new_position]
        if deed_owner:
            if deed_owner != player and not self.is_mortgaged[new_position]:
                amount = self.get_price(player, new_position)

                self.pay_up(player, deed_owner, amount)
                self.money_raised[new_position] += amount
        else:
            amount = self.prices.deed_cost[new_position]
            if player.buy_position(new_position, amount) and self.buy_deed(player, new_position):
                # player bought deed
                pass

            else:
                # auction off deed
                self.auction(new_position, self.prices.mortgage[new_position], self.bank)

    def auction(self, tile, initial_bid, initial_owner):
        amount = self.prices.deed_cost[tile]
        bid_changed = True

        current_bid = initial_bid, self.bank
        while bid_changed:
            bid_changed = False
            for player in self.players:
                if player != current_bid[1]:  # already highest bidder
                    bid = player.bid_position(tile, amount, current_bid[0])
                    if bid > current_bid[0] and bid <= self.players_cash[player]:
                        current_bid = (bid, player)
                        bid_changed = True

        if current_bid[0] > initial_bid:
            self.buy_deed(current_bid[1], tile, current_bid[0])
            return current_bid[0]

        return False

    def start_game(self, max_turns=100):
        for turn, p in enumerate(cycle(self.players)):
            if turn == max_turns:
                # print "Max turns reached, no winner after %d turns" % turn
                return False

            if not p.is_bankrupt:
                try:
                    if self.jail_turns_left[p]:
                        self.jail_turns_left[p] -= 1

                        d1, d2 = self.dice_roll()
                        if d1 != d2:
                            # third turn? pay_up and update position
                            if self.jail_turns_left[p] == 0:
                                self.pay_up(p, self.bank, 50)
                                self.update_position(p, d1, d2)

                            # stay in jail
                            else:
                                raise GoToJailException()
                        else:
                            self.jail_turns_left[p] = 0
                            self.update_position(p, d1, d2)
                    else:
                        for n in range(1, 4):
                            d1, d2 = self.dice_roll()

                            # rolled three times, and eyes are the same -> go to jail
                            if n == 3 and d1 == d2:
                                raise GoToJailException()

                            # update position
                            self.update_position(p, d1, d2)

                            if d1 != d2:
                                break

                except GoToJailException:
                    if self.position[p] != JAIL_TILE:
                        self.position[p] = JAIL_TILE
                        self.jail_turns_left[p] = 3
                    self.history[p].append(self.position[p])

                except BankruptException as b:
                    # print "Player", p, "went bankrupt", b, "caused by", b.caused_by
                    self.declare_bankrupt(p, b.caused_by)
                    self.caused_bankruptcy[self.position[p]] += 1

                    nr_active = sum(not p.is_bankrupt for p in self.players)
                    if nr_active == 1:
                        # print "Game finished after %d turns" % turn
                        return turn

            if not p.is_bankrupt:
                # anything else?
                p.anything_else()

    def declare_bankrupt(self, player, caused_by):
        assert not player.is_bankrupt
        player.is_bankrupt = True

        if caused_by != self.bank:
            self.players_cash[caused_by] += self.players_cash[player]
        self.players_cash[player] = 0

        for tile in self.get_deeds(player):
            # transfer to caused_by, if it failes transfer to bank
            if not self.transfer_deed(player, caused_by, tile):
                self.deed_owners[tile] = None
                self.is_mortgaged[tile] = False
                self.houses[tile] = 0

class Player(object):
    def __init__(self):
        self.is_bankrupt = False

    def buy_position(self, position, amount):
        return False

    def bid_position(self, position, amount, current_bid):
        return 0

    def anything_else(self):
        pass

    def sort_tiles(self, a, b):
        # prefer highest rent
        return cmp(self.board.prices.rent[b], self.board.prices.rent[a])

    def houses_wanted(self, tile):
        return 5

    def raise_amount(self, amount):
        for _ in range(5):
            # sell as few houses as possible
            my_houses = self.board.get_houses(self)
            houses_to_sell = 1
            while houses_to_sell < len(my_houses):
                for houses in combinations(my_houses, houses_to_sell):
                    raises_amount = sum(self.board.prices.house_cost[tile] / 2 for tile, nr_houses in houses)
                    if raises_amount >= amount:
                        # sell these houses
                        for tile, _ in houses:
                            self.board.sell_house(self, tile)
                        return

                houses_to_sell += 1

            raises_amount = sum(self.board.prices.house_cost[tile] / 2 for tile, nr_houses in my_houses)
            amount -= raises_amount
            for tile, _ in my_houses:
                self.board.sell_house(self, tile)

        my_deeds = self.board.get_mortgagable_deeds(self)
        my_deeds.sort(cmp=self.sort_tiles, reverse=True)

        # hold a public auction to raise at least more than the mortgage is worth
        for deed in my_deeds:
            amount_raised = self.board.auction(deed, self.board.prices.mortgage[deed] + 1, self)
            if amount_raised:
                amount -= amount_raised
                if amount <= 0:
                    return

        # mortgage as few deeds as possible
        deeds_to_sell = 1
        while deeds_to_sell < len(my_deeds):
            for deeds in combinations(my_deeds, deeds_to_sell):
                raises_amount = sum(self.board.prices.mortgage[deed] for deed in deeds)
                if raises_amount >= amount:
                    for deed in deeds:
                        self.board.add_mortgage(self, deed)
                    return

            deeds_to_sell += 1

        # didn't break, sell mortgage everything
        for deed in my_deeds:
            self.board.add_mortgage(self, deed)

class BuyAll(Player):

    def buy_position(self, position, amount):
        return True

    def bid_position(self, position, amount, current_bid):
        if self.buy_position(position, amount):
            # bid at most 10% of what I have left more than amount
            max = amount + self.board.get_cash_left(self) * 0.1
            if max > (current_bid + 1):
                 return current_bid + 1
        return 0

    def anything_else(self):
        # remove mortgages
        mortgages_owned = self.board.get_morgages_owned(self)
        mortgages_owned.sort(cmp=self.sort_tiles)

        for tile in mortgages_owned:
            self.board.sell_mortgage(self, tile)

        # add as many houses as possible
        streets_owned = self.board.get_streets_owned(self)
        while True:
            possible_tiles = []
            added_house = False

            for color in streets_owned:
                min_houses = min(self.board.houses[tile] for tile in self.board.prices.colors[color])
                for tile in self.board.prices.colors[color]:
                    if self.board.houses[tile] == min_houses and self.board.houses[tile] < self.houses_wanted(tile):
                        possible_tiles.append(tile)
            possible_tiles.sort(cmp=self.sort_tiles)

            for tile in possible_tiles:
                if self.board.add_house(self, tile):
                    added_house = True

            if not added_house:
                break

class BuyFrom(BuyAll):

    def __init__(self, start_index):
        super(BuyFrom, self).__init__()
        self.start_index = start_index

    def buy_position(self, position, amount):
        return position >= self.start_index

class BuyBetween(BuyFrom):

    def __init__(self, start_index, until_index):
        super(BuyBetween, self).__init__(start_index)
        self.until_index = until_index

    def buy_position(self, position, amount):
        return self.start_index <= position <= self.until_index

class GaPlayer(BuyAll):

    def __init__(self, bidding_list):
        super(GaPlayer, self).__init__()
        self.bidding_list = bidding_list

    def buy_position(self, position, amount):
        return self.bidding_list[position]

    def __str__(self):
        return "GaPlayer '%s'" % self.bidding_list

class GaHousePlayer(BuyAll):

    def __init__(self, bidding_list):
        super(GaHousePlayer, self).__init__()
        self.bidding_list = bidding_list

    def buy_position(self, position, amount):
        return self.bidding_list[position]

    def houses_wanted(self, tile):
        return self.bidding_list[tile] - 1

    def __str__(self):
        return "GaHousePlayer '%s'" % self.bidding_list

class Bank(object):
    pass

def print_game(b):
    for p in b.players:
        print type(p), b.get_cash_left(p), p.is_bankrupt

    for i, d in enumerate(b.deed_owners):
        print i, b.prices.name[i], d, b.is_mortgaged[i], b.houses[i], b.money_raised[i]

if __name__ == '__main__':
    won = defaultdict(int)
    nr_turns = defaultdict(int)
    money_raised = defaultdict(int)
    money_invested = defaultdict(int)
    caused_bankruptcy = defaultdict(int)
    for _ in range(1000):
        b = Board()
        turns = b.start_game(10000)
        if turns:
            for p in b.players:
                if not p.is_bankrupt:
                    won[type(p)] += 1
                    nr_turns[type(p)] += turns

            for tile, amount in enumerate(b.money_raised):
                money_raised[tile] += amount

            for tile, amount in enumerate(b.money_invested):
                money_invested[tile] += amount

            for tile, amount in enumerate(b.caused_bankruptcy):
                caused_bankruptcy[tile] += amount

        else:
            # print_game(b)
            pass

    for player, times in won.iteritems():
        print player, times, nr_turns[player] / times

    for tile, amount in money_raised.iteritems():
        print tile, amount, money_invested[tile], (amount / float(money_invested[tile])) if money_invested[tile] else 0, caused_bankruptcy[tile]

    b.prices.print_deeds([1, 1, 1, 1, 0, 1, 1, 0, 1, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 1, 0, 1])

#     b = Board()
#     b.start_game(10000)
#

