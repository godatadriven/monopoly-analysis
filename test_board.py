from unittest import TestCase
from monopoly import Player, Board, dice_roll

class TestBoard(TestCase):

    def setUp(self):
        self.p = Player()
        self.board = Board([self.p])

    def test_position_update(self):
        self.assertEqual(self.board.get_position(self.p), 0)

        d1, d2 = dice_roll()
        self.board.update_position(self.p, d1, d2)

        self.assertEqual(self.board.get_position(self.p), d1 + d2)

    def test_pass_start(self):
        self.board.update_position(self.p, 10, 15)
        self.board.update_position(self.p, 10, 15)
        self.assertEqual(self.board.get_cash_left(self.p), 1500 + 200)

    def test_buy_position(self):
        self.board.buy_deed(self.p, self.board.deeds[1])

        self.assertEqual(self.board.get_cash_left(self.p), 1500 - 60)
        self.assertEqual(self.board.get_deeds(self.p), [self.board.deeds[1], ])
        self.assertEqual(self.board.get_mortgagable_deeds(self.p), [self.board.deeds[1], ])
        self.assertEqual(self.board.get_streets_owned(self.p), [])

    def test_mortgage(self):
        self.board.buy_deed(self.p, self.board.deeds[1])
        self.board.add_mortgage(self.p, self.board.deeds[1])

        self.assertEqual(self.board.get_morgages_owned(self.p), [self.board.deeds[1], ])
        self.assertEqual(self.board.get_cash_left(self.p), 1500 - 60 + 30)
        self.assertEqual(self.board.get_mortgagable_deeds(self.p), [])

    def test_streets(self):
        self.board.buy_deed(self.p, self.board.deeds[1])
        self.board.buy_deed(self.p, self.board.deeds[3])
        self.assertEqual(self.board.get_streets_owned(self.p), ["purple"])

    def test_houses(self):
        self.board.buy_deed(self.p, self.board.deeds[1])
        self.board.buy_deed(self.p, self.board.deeds[3])

        cash_left = 1500 - 60 - 60
        self.assertEqual(self.board.get_cash_left(self.p), cash_left)

        self.board.add_house(self.p, self.board.deeds[1])
        self.board.add_house(self.p, self.board.deeds[1])

        cash_left -= 50

        self.assertEqual(self.board.get_houses(self.p), [(self.board.deeds[1], 1)])
        self.assertEqual(self.board.get_cash_left(self.p), cash_left)

        self.board.sell_house(self.p, self.board.deeds[1])

        cash_left += 25

        self.assertEqual(self.board.get_cash_left(self.p), cash_left)
        self.assertTrue(self.board.add_house(self.p, self.board.deeds[1]))

    def test_morgage_house(self):
        self.board.buy_deed(self.p, self.board.deeds[1])
        self.board.buy_deed(self.p, self.board.deeds[3])

        self.board.add_house(self.p, self.board.deeds[1])
        self.board.add_house(self.p, self.board.deeds[3])
        self.assertEqual(self.board.get_houses(self.p), [(self.board.deeds[1], 1), (self.board.deeds[3], 1)])

        self.assertFalse(self.board.add_mortgage(self.p, self.board.deeds[1]))
        self.board.sell_house(self.p, self.board.deeds[1])
        self.assertTrue(self.board.add_mortgage(self.p, self.board.deeds[1]))

