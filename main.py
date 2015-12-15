from random import randint
from collections import defaultdict
from itertools import cycle

JAIL_TILE = 10
GOTO_JAIL_TILE = 30

class GoToJailException(Exception):
    pass

class DeedPrices(object):

    def __init__(self):
        self.deed_cost = {}
        self.house_cost = {}
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

                self.rent[tile] = [int(deed['rent']),
                                   int(deed['house_1']),
                                   int(deed['house_2']),
                                   int(deed['house_3']),
                                   int(deed['house_4']),
                                   int(deed['hotel'])]

                self.color[tile] = deed['color']
                self.colors[deed['color']].append(tile)

class Board(object):

    def __init__(self):
        self.players = [Player(1500), BuyAll(1500), BuyFrom(1500, 10), BuyBetween(1500, 10, 20)]
        self.history = defaultdict(list)
        self.position = defaultdict(int)
        self.jail_turns_left = defaultdict(int)
        self.bank = Bank()
        self.prices = DeedPrices()

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

        self.houses = defaultdict(int)

    def get_price(self, position):
        if self.deed_owners[position] != self.bank:
            nr_houses = self.houses[position]
            if nr_houses == 0:
                color = self.prices.color[position]
                if all(self.deed_owners[tile] == self.deed_owners[position] for tile in self.prices.colors[color]):
                    # all houses owned by the same player?
                    return self.prices.rent[position][nr_houses] * 2
            return self.prices.rent[position][nr_houses]
        return 0

    def dice_roll(self):
        return randint(1, 6), randint(1, 6)

    def get_position(self, player):
        return self.position[player]

    def update_position(self, player, d1, d2):
        old_position = self.position[player]
        new_position = self.position[player] = (old_position + d1 + d2) % 40
        if new_position == GOTO_JAIL_TILE:
            raise GoToJailException()

        self.history[player].append(new_position)

        # passed start
        if old_position > new_position:
            player.receive_cash(200)

        # available for purchase?
        if self.deed_owners[new_position]:
            # no, maybe we have to pay?
            if self.deed_owners[new_position] != player:
                amount = self.get_price(new_position)
                player.pay_up(amount)

        else:
            amount = self.prices.deed_cost[new_position]
            if player.buy_position(new_position, amount):
                player.pay_up(amount)
                self.deed_owners[new_position] = player

            else:
                # action off deed
                pass

    def start_game(self, max_turns=100):
        for turn, p in enumerate(cycle(self.players)):
            if turn == max_turns:
                break

            try:
                if self.jail_turns_left[p]:
                    d1, d2 = self.dice_roll()

                    if d1 != d2:
                        self.jail_turns_left[p] = self.jail_turns_left[p] - 1
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
                    self.jail_turns_left[p] = 2
                self.history[p].append(self.position[p])

class Player(object):
    def __init__(self, cash_left):
        self.cash_left = cash_left

    def buy_position(self, position, price):
        return False

    def pay_up(self, amount):
        self.cash_left -= amount

    def receive_cash(self, amount):
        self.cash_left += amount

class BuyAll(Player):

    def buy_position(self, position, price):
        return self.cash_left - price > 0

class BuyFrom(BuyAll):

    def __init__(self, cash_left, start_index):
        super(BuyFrom, self).__init__(cash_left)
        self.start_index = start_index

    def buy_position(self, position, price):
        if position >= self.start_index:
            return super(BuyFrom, self).buy_position(position, price)
        return False

class BuyBetween(BuyFrom):

    def __init__(self, cash_left, start_index, until_index):
        super(BuyBetween, self).__init__(cash_left, start_index)
        self.until_index = until_index

    def buy_position(self, position, price):
        if super(BuyBetween, self).buy_position(position, price):
            return position < self.until_index
        return False

class Bank(object):
    pass

if __name__ == '__main__':
    b = Board()
    b.start_game(1000)

    for p in b.players:
        print p, p.cash_left


    for i, d in enumerate(b.deed_owners):
        print i, d
