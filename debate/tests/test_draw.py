import os.path, sys
if os.path.abspath("..") not in sys.path: sys.path.append(os.path.abspath(".."))
import unittest
from collections import OrderedDict
import draw
import copy

class TestPowerPairedDrawParts(unittest.TestCase):
    """Basic unit test for core functionality of power-paired draws.
    Nowhere near comprehensive."""

    brackets = OrderedDict([
        (4, [1, 2, 3, 4, 5]),
        (3, [6, 7, 8, 9]),
        (2, [10, 11, 12, 13, 14]),
        (1, [15, 16])
    ])

    def setUp(self):
        self.b2 = copy.deepcopy(self.brackets)
        self.ppd = draw.PowerPairedDraw(None)

    def tearDown(self):
        self.b2 = None
        self.ppd = None

    def bracket(self, name, expected):
        self.ppd.options["odd_bracket"] = name
        self.ppd.resolve_odd_brackets(self.b2)
        self.assertEqual(self.b2, expected)

    def test_pullup_top(self):
        self.bracket("pullup_top", OrderedDict([
            (4, [1, 2, 3, 4, 5, 6]),
            (3, [7, 8, 9, 10]),
            (2, [11, 12, 13, 14]),
            (1, [15, 16])
        ]))

    def test_pullup_bottom(self):
        self.bracket("pullup_bottom", OrderedDict([
            (4, [1, 2, 3, 4, 5, 9]),
            (3, [6, 7, 8, 14]),
            (2, [10, 11, 12, 13]),
            (1, [15, 16])
        ]))

    def test_pullup_intermediate(self):
        self.bracket("intermediate", OrderedDict([
            (4, [1, 2, 3, 4]),
            (3.5, [5, 6]),
            (3, [7, 8]),
            (2.5, [9, 10]),
            (2, [11, 12, 13, 14]),
            (1, [15, 16])
        ]))

    def test_pullup_random(self):
        for j in range(5):
            b2 = self.b2
            self.ppd.options["odd_bracket"] = "pullup_random"
            self.ppd.resolve_odd_brackets(b2)
            self.assertTrue(all(i in b2[4] for i in [1, 2, 3, 4, 5]))
            self.assertEqual([i in b2[4] for i in [6, 7, 8, 9]].count(True), 1)
            self.assertEqual([i in b2[3] for i in [6, 7, 8, 9]].count(True), 3)
            self.assertEqual([i in b2[3] for i in [10, 11, 12, 13, 14]].count(True), 1)
            self.assertEqual([i in b2[2] for i in [10, 11, 12, 13, 14]].count(True), 4)
            self.assertEqual([15, 16], b2[1])

    def pairings(self, name, expected):
        ppd = self.ppd
        ppd.options["odd_bracket"] = "pullup_top"
        ppd.options["pairing_method"] = name
        ppd.resolve_odd_brackets(self.b2)
        pairings = ppd.generate_pairings(self.b2)
        pairings_list = list()
        for bracket in pairings.itervalues():
            pairings_list.extend(bracket)
        result = tuple(tuple(p.teams) for p in pairings_list)
        self.assertEqual(result, expected)

    def test_pairings_fold(self):
        self.pairings("fold", (
            (1, 6), (2, 5), (3, 4), (7, 10), (8, 9), (11, 14), (12, 13), (15, 16)
        ))

    def test_pairings_slide(self):
        self.pairings("slide", (
            (1, 4), (2, 5), (3, 6), (7, 9), (8, 10), (11, 13), (12, 14), (15, 16)
        ))


    def one_up_one_down(self, data, expected, **options):
        from test_one_up_one_down import TestTeam
        for option, value in options.iteritems():
            self.ppd.options[option] = value
        pairings = []
        for data1, data2 in data:
            team1 = TestTeam(*data1)
            team2 = TestTeam(*data2)
            pairing = draw.Pairing([team1, team2], None, None)
            pairings.append(pairing)
        pairings_dict = {0: pairings}
        self.ppd.avoid_conflicts(pairings_dict)
        self.assertEqual(len(expected), len(pairings))
        for (exp_teams, exp_flags), pair in zip(expected, pairings):
            self.assertEqual(tuple(t.id for t in pair.teams), exp_teams)
            self.assertEqual(pair.flags, exp_flags)

    @staticmethod
    def _1u1d_no_change(data):
        return [((t1[0], t2[0]), []) for t1, t2 in data]

    def test_no_swap(self):
        data = (((1, 'A'), (5, 'B')),
                ((2, 'C'), (6, 'A')),
                ((3, 'B'), (7, 'D')),
                ((4, 'C'), (8, 'A')))
        expected = self._1u1d_no_change(data)
        self.one_up_one_down(data, expected)

    def test_swap_institution(self):
        data = (((1, 'A'), (5, 'A')),
                ((2, 'C'), (6, 'B')),
                ((3, 'B'), (7, 'D')),
                ((4, 'C'), (8, 'A')))
        expected = [((1, 6), ["1u1d_institution"]),
                    ((2, 5), ["1u1d_other"]),
                    ((3, 7), []),
                    ((4, 8), [])]
        self.one_up_one_down(data, expected)

    def test_no_swap_institution(self):
        data = (((1, 'A'), (5, 'A')),
                ((2, 'C'), (6, 'B')),
                ((3, 'B'), (7, 'D')),
                ((4, 'C'), (8, 'A')))
        expected = self._1u1d_no_change(data)
        self.one_up_one_down(data, expected, avoid_institution=False)

    def test_swap_history(self):
        data = (((1, 'A', None, 5), (5, 'B')),
                ((2, 'C'), (6, 'A')),
                ((3, 'B'), (7, 'D')),
                ((4, 'C'), (8, 'A')))
        expected = [((1, 6), ["1u1d_history"]),
                    ((2, 5), ["1u1d_other"]),
                    ((3, 7), []),
                    ((4, 8), [])]
        self.one_up_one_down(data, expected)

    def test_no_swap_history(self):
        data = (((1, 'A', None, 5), (5, 'B')),
                ((2, 'C'), (6, 'A')),
                ((3, 'B'), (7, 'D')),
                ((4, 'C'), (8, 'A')))
        expected = self._1u1d_no_change(data)
        self.one_up_one_down(data, expected, avoid_history=False)

    def test_last_swap(self):
        data = (((1, 'A'), (5, 'B')),
                ((2, 'C'), (6, 'A')),
                ((3, 'B'), (7, 'D')),
                ((4, 'C', None, 8), (8, 'A')))
        expected = [((1, 5), []),
                    ((2, 6), []),
                    ((3, 8), ["1u1d_other"]),
                    ((4, 7), ["1u1d_history"])]
        self.one_up_one_down(data, expected)

class TestPowerPairedDraw(unittest.TestCase):
    """Test the entire draw functions as a black box."""

    standings = [(12, 'B', 4, [26, 11, 15, 14], 2),
                 (2, 'D', 3, [22, 16, 20, 10], 2),
                 (3, 'E', 3, [23, 20, 25, 4], 2),
                 (4, 'B', 3, [18, 25, 5, 3], 3),
                 (6, 'E', 3, [19, 15, 18, 9], 2),
                 (8, 'A', 3, [15, 24, 1, 15], 2),
                 (11, 'B', 3, [1, 12, 23, 22], 2),
                 (14, 'A', 3, [24, 17, 9, 12], 2),
                 (17, 'E', 3, [21, 14, 7, 25], 2),
                 (7, 'D', 2, [16, 9, 17, 16], 2),
                 (9, 'D', 2, [5, 7, 14, 6], 2),
                 (15, 'B', 2, [8, 6, 12, 8], 2),
                 (18, 'B', 2, [4, 21, 6, 21], 2),
                 (22, 'A', 2, [2, 10, 16, 11], 2),
                 (23, 'A', 2, [3, 19, 11, 5], 2),
                 (24, 'B', 2, [14, 8, 19, 20], 3),
                 (25, 'A', 2, [10, 4, 3, 17], 3),
                 (1, 'C', 1, [11, 26, 8, 19], 2),
                 (5, 'C', 1, [9, 13, 4, 23], 1),
                 (10, 'B', 1, [25, 22, 13, 2], 1),
                 (16, 'D', 1, [7, 2, 22, 7], 2),
                 (19, 'B', 1, [6, 23, 24, 1], 1),
                 (20, 'E', 1, [13, 3, 2, 24], 2),
                 (21, 'A', 1, [17, 18, 26, 18], 2),
                 (26, 'B', 1, [12, 1, 21, 13], 2),
                 (13, 'C', 0, [20, 5, 10, 26], 2)]

    expected = (12, 2),
            (3, 4),
            (11, 14),
            (6, 8),
            (17, 7),
            (9, 23),
            (15, 24),
            (18, 25),
            (22, 1),
            (5, 21),
            (10, 19),
            (16, 26),
            (20, 13),


    def do_draw(self):
        from test_one_up_one_down import TestTeam
        standings = [TestTeam(*args) for args in self.standings]
        self.ppd = draw.PowerPairedDraw(standings)
        return self.ppd.get_draw()

    def test_draw(self):
        draw = self.do_draw()
        print draw

if __name__ == '__main__':
    unittest.main()