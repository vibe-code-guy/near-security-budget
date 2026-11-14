import unittest

from pipeline import c1


class EffectiveMaximum(unittest.TestCase):
    def test_fixed_maximum(self):
        self.assertEqual(c1.effective_max("live", 300000.0, None, 5e7), (300000.0, "live", False))

    def test_percentage_leg_binds_and_is_flagged_derived(self):
        self.assertEqual(c1.effective_max("live", 1_000_000.0, 10.0, 2e6), (200000.0, "live", True))

    def test_cap_binds(self):
        self.assertEqual(c1.effective_max("live", 300000.0, 10.0, 1e9), (300000.0, "live", False))

    def test_percentage_without_cap(self):
        self.assertEqual(c1.effective_max("live", None, 10.0, 1e6), (100000.0, "live", True))

    def test_none_found_is_zero_and_no_usd_figure_is_undetermined(self):
        self.assertEqual(c1.effective_max("none_found", None, None, 1e6), (0.0, "none_found", False))
        self.assertEqual(c1.effective_max("live", None, None, 1e6), (None, "undetermined", False))

    def test_number_parsing(self):
        self.assertEqual(c1.num("$1,000,000"), 1e6)
        self.assertEqual(c1.num("10%"), 10.0)
        self.assertIsNone(c1.num(""))


class Bands(unittest.TestCase):
    def test_band_edges(self):
        self.assertEqual([c1.band_of(x) for x in (5e6, 1e7, 9.9e7, 1e8, 1e9, 5e9)], [0, 1, 1, 2, 3, 3])

    def test_small_band_merges_into_the_one_below(self):
        self.assertEqual(c1.merge_bands([10, 12, 11, 2]), [[0], [1], [2, 3]])

    def test_lowest_band_merges_upward(self):
        self.assertEqual(c1.merge_bands([1, 12, 11, 9]), [[0, 1], [2], [3]])

    def test_merging_repeats(self):
        self.assertEqual(c1.merge_bands([1, 1, 20, 2]), [[0, 1, 2, 3]])

    def test_labels(self):
        self.assertEqual(c1.band_label([0]), "under $10M")
        self.assertEqual(c1.band_label([2, 3]), "over $100M")
        self.assertEqual(c1.band_label([1]), "$10M to $100M")


RULES = {"not_live_counts_as_zero": {"label": "not a live public bounty", "rows": {"Sui/x": "invite-only", "Solana/j": "dead link"}},
         "none_found_search_incomplete": {"label": "none found, search incomplete", "rows": {"Solana/s": "one source not checked"}},
         "sensitivity_undetermined_instead_of_zero": ["Solana/s", "Solana/j"]}


class StatusRules(unittest.TestCase):
    def test_rule_a_not_live_counts_as_zero(self):
        self.assertEqual(c1.resolve_status("not checked", "Sui/x", RULES)[::2], ("none_found", "a"))
        self.assertEqual(c1.resolve_status("undetermined", "Sui/x", RULES)[::2], ("none_found", "a"))

    def test_rule_b_incomplete_search_counts_as_zero_with_label(self):
        status, label, rule = c1.resolve_status("not checked", "Solana/s", RULES)
        self.assertEqual((status, rule), ("none_found", "b"))
        self.assertIn("search incomplete", label)

    def test_rule_c_other_unchecked_rows_are_undetermined_never_zero(self):
        self.assertEqual(c1.resolve_status("not checked", "Base/y", RULES)[::2], ("undetermined", "c"))

    def test_entered_statuses_pass_through(self):
        self.assertEqual(c1.resolve_status("live", "Near/z", RULES)[0], "live")
        self.assertEqual(c1.resolve_status("none found", "Near/z", RULES)[0], "none_found")

    def test_sensitivity_turns_rule_b_rows_and_jito_into_undetermined(self):
        self.assertEqual(c1.resolve_status("not checked", "Solana/s", RULES, sensitivity=True)[0], "undetermined")
        self.assertEqual(c1.resolve_status("not checked", "Solana/j", RULES, sensitivity=True)[0], "undetermined")
        self.assertEqual(c1.resolve_status("not checked", "Sui/x", RULES, sensitivity=True)[0], "none_found")


class Verdict(unittest.TestCase):
    cov = {"Near": 40.0, "Solana": 60.0, "Sui": 50.0, "Aptos": 20.0, "Base": 90.0}
    none = {"Near": 0.0, "Solana": 0.0, "Sui": 0.0, "Aptos": 0.0, "Base": 0.0}

    def test_coverage_more_than_ten_points_below_median_fails(self):
        v = c1.claim_verdict(self.cov, self.none, 80.0)  # peer median 55
        self.assertEqual((v["c1a"], v["c1b"], v["verdict"]), ("fails", "holds", "fails"))

    def test_score_below_half_fails(self):
        v = c1.claim_verdict({**self.cov, "Near": 50.0}, self.none, 49.9)
        self.assertEqual((v["c1a"], v["c1b"], v["verdict"]), ("holds", "fails", "fails"))

    def test_holds_when_neither_fails(self):
        self.assertEqual(c1.claim_verdict({**self.cov, "Near": 45.0}, self.none, 50.0)["verdict"], "holds")

    def test_undetermined_rows_make_it_cant_tell(self):
        self.assertEqual(c1.claim_verdict(self.cov, {**self.none, "Near": 21.0}, 80.0)["verdict"], "can't tell")
        self.assertEqual(c1.claim_verdict(self.cov, {**self.none, "Sui": 30.0, "Base": 25.0}, 80.0)["verdict"], "can't tell")
        self.assertEqual(c1.claim_verdict({**self.cov, "Near": 50.0}, {**self.none, "Sui": 30.0}, 80.0)["verdict"], "holds")


if __name__ == "__main__":
    unittest.main()
