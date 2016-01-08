from unittest import TestCase
from monopoly import Player, Board

class TestBoard(TestCase):

    def setUp(self):
        self.p = Player()
        self.board = Board([self.p])

    def test_raise_amount_mortgage(self):
        self.board.buy_position(self.p, 1)
        self.board.buy_position(self.p, 3)

        self.p.raise_amount(30)
        self.assertEqual(self.board.get_mortgagable_deeds(self.p), [3, ])

        self.p.raise_amount(30)
        self.assertEqual(self.board.get_mortgagable_deeds(self.p), [])

    def test_raise_amount_houses(self):
        self.board.buy_position(self.p, 1)
        self.board.buy_position(self.p, 3)

        self.board.add_house(self.p, "purple")
        self.board.add_house(self.p, "purple")

        self.assertEqual(self.board.get_mortgagable_deeds(self.p), [])

        self.p.raise_amount(25)
        self.assertEqual(self.board.get_houses(self.p), [(3, 1)])
        self.assertEqual(self.board.get_mortgagable_deeds(self.p), [1, ])
