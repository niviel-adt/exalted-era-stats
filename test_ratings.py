import unittest

from ratings import InvalidStats, calculate_rating, validate_rating_stats


class RatingTests(unittest.TestCase):
    def setUp(self):
        self.stats = dict(acs=300, kd_ratio=1.5, headshot_percentage=30,
                          kills=120, total_matches=10, first_bloods=20)

    def test_repeatable_and_numeric_strings(self):
        expected = (100.0, "S")
        for _ in range(20):
            self.assertEqual(calculate_rating(self.stats), expected)
        self.assertEqual(calculate_rating({k: str(v) for k, v in self.stats.items()}), expected)

    def test_missing_fields_do_not_become_zero(self):
        for field in self.stats:
            with self.subTest(field=field), self.assertRaises(InvalidStats):
                calculate_rating({**self.stats, field: None})
        with self.assertRaises(InvalidStats):
            calculate_rating({})

    def test_bad_values(self):
        for value in (True, False, float("nan"), float("inf"), -1, "unreadable", [], {}):
            with self.subTest(value=value), self.assertRaises(InvalidStats):
                calculate_rating({**self.stats, "acs": value})
        for field, value in (("kills", 1.5), ("total_matches", 0),
                             ("headshot_percentage", 101), ("first_bloods", 121)):
            with self.subTest(field=field), self.assertRaises(InvalidStats):
                calculate_rating({**self.stats, field: value})

    def test_zero_is_valid_when_matches_exist(self):
        stats = {k: 0 for k in self.stats}
        stats["total_matches"] = 10
        self.assertEqual(calculate_rating(stats), (0.0, "D"))

    def test_grade_boundaries_match_displayed_score(self):
        for fraction, grade in ((.9, "S"), (.8, "A"), (.7, "B"), (.6, "C"), (.5, "D")):
            stats = {**self.stats, "acs": 300*fraction, "kd_ratio": 1.5*fraction,
                     "headshot_percentage": 30*fraction, "kills": int(120*fraction),
                     "first_bloods": int(20*fraction)}
            self.assertEqual(calculate_rating(stats), (100*fraction, grade))

    def test_normalization_does_not_mutate_input(self):
        stats = {**self.stats, "kills": "120"}
        self.assertEqual(validate_rating_stats(stats)["kills"], 120)
        self.assertEqual(stats["kills"], "120")


if __name__ == "__main__":
    unittest.main()
