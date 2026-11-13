import unittest

from pipeline import c2

BY_ID = {
    "1": {"chainTvls": {"Near": 86.0, "Ethereum": 58.0, "Near-staking": 500.0, "borrowed": 900.0}},
    "2": {"chainTvls": {"Base": 10.0, "Arbitrum": 10.0}},  # tie: no largest chain
    "3": {"chainTvls": {}},  # dead protocol
}


class Attribution(unittest.TestCase):
    def test_largest_chain_ignores_suffixed_and_non_chain_keys(self):
        self.assertEqual(c2.plurality_chain(BY_ID["1"]), "Near")
        self.assertIsNone(c2.plurality_chain(BY_ID["2"]))
        self.assertIsNone(c2.plurality_chain(BY_ID["3"]))

    def test_protocol_id_route_goes_to_one_chain_only(self):
        h = {"chain": ["BSC"], "defillamaId": "1"}  # shape of the 2026-10-01 NEAR Intents row
        self.assertEqual(c2.attribute(h, "Near", BY_ID), ("lower", "protocol_id"))
        self.assertEqual(c2.attribute(h, "Base", BY_ID), (None, None))

    def test_single_tag_is_lower_bound_and_case_insensitive(self):
        self.assertEqual(c2.attribute({"chain": ["NEAR"]}, "Near", BY_ID), ("lower", "tag_single"))

    def test_multi_chain_tag_is_upper_bound_only(self):
        h = {"chain": ["Base", "Arbitrum", "Optimism"], "defillamaId": None}
        self.assertEqual(c2.attribute(h, "Base", BY_ID), ("upper", "tag_multi"))
        self.assertEqual(c2.attribute(h, "Solana", BY_ID), (None, None))

    def test_non_numeric_ids_do_not_route(self):
        h = {"chain": ["Initia"], "defillamaId": "chain#initia"}
        self.assertEqual(c2.attribute(h, "Near", BY_ID), (None, None))

    def test_untagged_hack_is_unattributed(self):
        self.assertEqual(c2.attribute({"chain": None}, "Near", BY_ID), (None, None))


class Rates(unittest.TestCase):
    def test_loss_rate_is_annualised_over_730_days(self):
        self.assertAlmostEqual(c2.loss_rate(20.0, 100.0), 10.0)

    def test_window_and_mean(self):
        start, end = c2.window("2026-11-13")
        self.assertEqual((end - start) // 86400, 730)
        hist = [{"date": start, "tvl": 999}, {"date": start + 86400, "tvl": 10}, {"date": end, "tvl": 30}]
        self.assertEqual(c2.mean_tvl(hist, start, end), (20.0, 2))

    def test_verdict_rule(self):
        peers = [{"lower": 1, "upper": 2}, {"lower": 2, "upper": 3}, {"lower": 3, "upper": 4}, {"lower": 4, "upper": 5}]
        self.assertEqual(c2.verdict({"lower": 9, "upper": 9}, peers)["verdict"], "fails")
        self.assertEqual(c2.verdict({"lower": 2.5, "upper": 3.5}, peers)["verdict"], "holds")  # at the median
        self.assertEqual(c2.verdict({"lower": 1, "upper": 9}, peers)["verdict"], "can't tell")


if __name__ == "__main__":
    unittest.main()
