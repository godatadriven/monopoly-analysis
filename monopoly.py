from random import randint
from collections import defaultdict
from itertools import cycle, combinations
from __builtin__ import False

JAIL_TILE = 10
GOTO_JAIL_TILE = 30

def dice_roll():
    return randint(1, 6), randint(1, 6)

class GoToJailException(Exception):
    pass

class BankruptException(Exception):

    def __init__(self, msg, caused_by):
        super(BankruptException, self).__init__(msg)
        self.caused_by = caused_by

class Deed(object):

    def __init__(self, name, tile, deed_cost, house_cost, rent):
        self.name = name
        self.tile = tile
        self.deed_cost = int(deed_cost)
        self.house_cost = int(house_cost)
        self.rent = map(int, rent)

        self.owner = None
        self.street = None

        self.is_mortgaged = False
        self.houses = 0

    @property
    def mortgage(self):
        return self.deed_cost / 2

    def is_owned(self, player):
        return self.owner == player

    def can_mortgage(self, player):
        return not self.is_mortgaged and self.houses == 0 and self.owner == player

    def get_price(self, player):
        if self.owner and self.owner != player and not self.is_mortgaged:
            if self.street.color == 'rr':
                nr_owned = self.street.nr_owned(self.owner)
                return self.rent[nr_owned]

            if self.street.color == 'utility':
                nr_owned = self.street.nr_owned(self.owner)
                d1, d2 = dice_roll()
                return self.rent[nr_owned] * (d1 + d2)
            
            if self.houses == 0 and self.street.is_owned(self.owner):
                # all houses owned by the same player?
                return self.rent[0] * 2
            return self.rent[self.houses]
        return 0


class NotSpecial(Deed):

    def __init__(self):
        super(NotSpecial, self).__init__("not special", -1, 0, 0, [])

    def get_price(self, player):
        return 0


class IncomeTax(Deed):

    def __init__(self, board):
        super(IncomeTax, self).__init__("income tax", -1, 0, 0, [])
        self.board = board

    def get_price(self, player):
        cash_left = self.board.get_cash_left(player)
        return min(200, cash_left * 0.1)


class LuxuryTax(Deed):

    def __init__(self):
        super(LuxuryTax, self).__init__("luxury tax", -1, 0, 0, [])

    def get_price(self, player):
        return 75


class Street(object):

    def __init__(self, color):
        self.color = color
        self.deeds = []

    def add_deed(self, deed):
        self.deeds.append(deed)
        deed.street = self
    
    def is_owned(self, player):
        return all(deed.owner == player for deed in self.deeds)
    
    def nr_owned(self, player):
        return sum(deed.owner == player for deed in self.deeds)
    
    def can_add_house(self, player):
        if not self.color in ('rr', 'utility'):
            return all(not deed.is_mortgaged for deed in self.deeds)
        return False 

            
class DeedPrices(object):

    @staticmethod
    def load_deeds():
        deeds = defaultdict(NotSpecial)
        streets = {}

        with open("monopoly.csv") as f:
            header = f.readline().rstrip().split(",")
            for line in f:
                deed = dict(zip(header, line.rstrip().split(",")))

                tile = int(deed['tile'])

                rents = [deed['rent'], deed['house_1'], deed['house_2'], deed['house_3'], deed['house_4'], deed['hotel']]
                deeds[tile] = Deed(deed['name'], tile, deed['deed_cost'], deed['house_cost'], rents)

                if not deed['color'] in streets:
                    streets[deed['color']] = Street(deed['color'])
                streets[deed['color']].add_deed(deeds[tile])

        return deeds, streets


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
        self.deeds, self.streets = DeedPrices.load_deeds()
        self.players_cash = dict((player, 1500) for player in self.players)

        self.deeds[4] = IncomeTax(self)
        self.deeds[38] = LuxuryTax()

        for index in [0, 10, 20, 30, 40, 2, 4, 7, 17, 22, 33, 36, 38]:
            self.deeds[index].owner = self.bank

        self.money_raised = [0] * 40
        self.money_invested = [0] * 40
        self.caused_bankruptcy = [0] * 40
        self.landed_on = [0] * 40

    def get_position(self, player):
        return self.position[player]

    def buy_deed(self, player, deed, amount=None):
        if deed.owner is None:
            if amount is None:
                amount = deed.deed_cost

            cash_left = self.players_cash[player]

            if cash_left >= amount:
                deed.owner = player
                self.players_cash[player] -= amount
                self.money_invested[deed.tile] += amount

                return True
        return False

    def transfer_deed(self, player, other_player, deed):
        if deed.is_owned(player):
            if deed.houses == 0 and other_player != self.bank:
                # need to pay 10% interest over mortgaged properties
                if deed.is_mortgaged:
                    amount = deed.deed_cost * .1
                else:
                    amount = 0

                cash_left = self.players_cash[player]
                if cash_left > amount:
                    deed.owner = other_player
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
        return [deed for deed in self.deeds.itervalues() if deed.is_owned(player)]

    def get_mortgagable_deeds(self, player):
        return [deed for deed in self.deeds.itervalues() if deed.can_mortgage(player)]

    def get_morgages_owned(self, player):
        return [deed for deed in self.deeds.itervalues() if deed.is_owned(player) and deed.is_mortgaged]

    def get_houses(self, player):
        return [(deed, deed.houses) for deed in self.deeds.itervalues() if deed.is_owned(player) and deed.houses > 0]

    def get_streets_owned(self, player):
        return [color for color, street in self.streets.iteritems() if street.is_owned(player)]

    def add_mortgage(self, player, deed):
        if deed.can_mortgage(player):
            deed.is_mortgaged = True
            self.players_cash[player] += deed.mortgage
            return True
        return False

    def sell_mortgage(self, player, deed):
        if deed.is_owned(player):
            cost = deed.mortgage * 1.1
            if self.players_cash[player] > cost:
                deed.is_mortgaged = False
                self.players_cash[player] -= cost

    def add_house(self, player, deed):
        if deed.street.can_add_house(player):
            houses_build = deed.houses
            min_houses_build = min(otherdeed.houses for otherdeed in deed.street.deeds)

            if houses_build == min_houses_build and houses_build < 5:
                if houses_build < 4:
                    nr_houses_sold = sum(deed.houses for deed in self.deeds.itervalues() if deed.houses < 5)
                    if nr_houses_sold >= 32:
                        return False

                if houses_build == 4:
                    nr_hotels_sold = sum(deed.houses == 5 for deed in self.deeds.itervalues())
                    if nr_hotels_sold >= 12:
                        return False

                cost = deed.house_cost
                if self.players_cash[player] > cost:
                    deed.houses += 1
                    self.players_cash[player] -= cost
                    self.money_invested[deed.tile] += cost
                    return True
        return False

    def sell_house(self, player, deed):
        if deed.is_owned(player) and deed.houses > 0:
            deed.houses -= 1
            self.players_cash[player] += deed.house_cost / 2
            return True
        return False

    def get_house_price(self, color):
        return self.streets[color].deeds[0].house_cost

    def update_position(self, player, d1, d2):
        old_position = self.position[player]
        new_position = self.position[player] = (old_position + d1 + d2) % 40
        if new_position == GOTO_JAIL_TILE:
            raise GoToJailException()

        self.history[player].append(new_position)
        self.landed_on[new_position] += 1

        # passed start
        if old_position > new_position:
            self.players_cash[player] += 200

        # available for purchase?
        deed = self.deeds[new_position]
        if deed.owner:
            if deed.owner != player:
                amount = deed.get_price(player)

                self.pay_up(player, deed.owner, amount)
                self.money_raised[new_position] += amount

        else:
            amount = deed.deed_cost
            if not (player.buy_position(deed, amount) and self.buy_deed(player, deed)):
                # player did not buy deed, auction
                self.auction(deed, deed.mortgage, self.bank)

    def auction(self, deed, initial_bid, initial_owner):
        amount = deed.deed_cost
        bid_changed = True

        current_bid = initial_bid, self.bank
        while bid_changed:
            bid_changed = False
            for player in self.players:
                if player != current_bid[1]:  # already highest bidder
                    bid = player.bid_position(deed, amount, current_bid[0])
                    if bid > current_bid[0] and bid <= self.players_cash[player]:
                        current_bid = (bid, player)
                        bid_changed = True

        if current_bid[0] > initial_bid:
            self.buy_deed(current_bid[1], deed, current_bid[0])
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

                        d1, d2 = dice_roll()
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
                            d1, d2 = dice_roll()

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
            # transfer to caused_by, if it fails transfer to bank
            if not self.transfer_deed(player, caused_by, tile):
                deed = self.deeds[tile]
                deed.owner = None
                deed.is_mortgaged = False
                deed.houses = 0

class Player(object):
    def __init__(self):
        self.is_bankrupt = False

    def buy_position(self, deed, amount):
        return False

    def bid_position(self, deed, amount, current_bid):
        return 0

    def anything_else(self):
        pass

    def sort_tiles(self, a, b):
        # prefer highest rent
        return cmp(b.rent[0], a.rent[0])

    def houses_wanted(self, tile):
        return 5

    def raise_amount(self, amount):
        for _ in range(5):
            # sell as few houses as possible
            my_houses = self.board.get_houses(self)
            houses_to_sell = 1
            while houses_to_sell < len(my_houses):
                for houses in combinations(my_houses, houses_to_sell):
                    raises_amount = sum(deed.house_cost / 2 for deed, nr_houses in houses)
                    if raises_amount >= amount:
                        # sell these houses
                        for deed, _ in houses:
                            self.board.sell_house(self, deed)
                        return

                houses_to_sell += 1

            raises_amount = sum(deed.house_cost / 2 for deed, nr_houses in my_houses)
            amount -= raises_amount
            for deed, _ in my_houses:
                self.board.sell_house(self, deed)

        my_deeds = self.board.get_mortgagable_deeds(self)
        my_deeds.sort(cmp=self.sort_tiles, reverse=True)

        # hold a public auction to raise at least more than the mortgage is worth
        for deed in my_deeds:
            amount_raised = self.board.auction(deed, deed.mortgage + 1, self)
            if amount_raised:
                amount -= amount_raised
                if amount <= 0:
                    return

        # mortgage as few deeds as possible
        deeds_to_sell = 1
        while deeds_to_sell < len(my_deeds):
            for deeds in combinations(my_deeds, deeds_to_sell):
                raises_amount = sum(deed.mortgage for deed in deeds)
                if raises_amount >= amount:
                    for deed in deeds:
                        self.board.add_mortgage(self, deed)
                    return

            deeds_to_sell += 1

        # didn't break, sell mortgage everything
        for deed in my_deeds:
            self.board.add_mortgage(self, deed)

    def __str__(self):
        return "Player"

class BuyAll(Player):

    def buy_position(self, deed, amount):
        return True

    def bid_position(self, deed, amount, current_bid):
        if self.buy_position(deed, amount):
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
                min_houses = min(otherdeed.houses for otherdeed in self.board.streets[color].deeds)

                for deed in self.board.streets[color].deeds:
                    if deed.houses == min_houses and deed.houses < self.houses_wanted(deed.tile):
                        possible_tiles.append(deed)
            possible_tiles.sort(cmp=self.sort_tiles)

            for deed in possible_tiles:
                if self.board.add_house(self, deed):
                    added_house = True

            if not added_house:
                break

    def __str__(self):
        return "BuyAll"

class BuyFrom(BuyAll):

    def __init__(self, start_index):
        super(BuyFrom, self).__init__()
        self.start_index = start_index

    def buy_position(self, position, amount):
        return position >= self.start_index

    def __str__(self):
        return "BuyFrom '%d'" % self.start_index


class BuyBetween(BuyFrom):

    def __init__(self, start_index, until_index):
        super(BuyBetween, self).__init__(start_index)
        self.until_index = until_index

    def buy_position(self, position, amount):
        return self.start_index <= position <= self.until_index

    def __str__(self):
        return "BuyBetween '%d-%d'" % (self.start_index, self.until_index)

class GaPlayer(BuyAll):

    def __init__(self, chromosome):
        super(GaPlayer, self).__init__()
        self.bidding_list = map(int, chromosome.split(","))

    def buy_position(self, deed, amount):
        return self.bidding_list[deed.tile]

    def __str__(self):
        return "GaPlayer '%s'" % self.bidding_list

class GaHousePlayer(BuyAll):

    def __init__(self, chromosome):
        super(GaHousePlayer, self).__init__()
        self.bidding_list = map(int, chromosome.split(","))

    def buy_position(self, deed, amount):
        return self.bidding_list[deed.tile]

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
    landed_on = defaultdict(int)

    for _ in range(1000):
        players = [Player(), BuyAll(), BuyFrom(10), BuyBetween(10, 20)]

        b = Board(players)
        turns = b.start_game(1000)
        if turns:
            for p in b.players:
                if not p.is_bankrupt:
                    won[str(p)] += 1
                    nr_turns[str(p)] += turns

            for tile, amount in enumerate(b.money_raised):
                money_raised[tile] += amount

            for tile, amount in enumerate(b.money_invested):
                money_invested[tile] += amount

            for tile, amount in enumerate(b.caused_bankruptcy):
                caused_bankruptcy[tile] += amount

            for tile, amount in enumerate(b.landed_on):
                landed_on[tile] += amount

        else:
            # print_game(b)
            pass

    for player, times in won.iteritems():
        print player, times, nr_turns[player] / times

    for tile, amount in money_raised.iteritems():
        print tile, int(amount), money_invested[tile], (amount / float(money_invested[tile])) if money_invested[tile] else 0, caused_bankruptcy[tile], landed_on[tile]
