import unittest

from pipeline import c3


def row(slug, tvl, signers, delay, readable=True):
    return {"slug": slug, "tvl": tvl, "readable": readable, "min_signers": signers, "delay": delay}


class Thresholds(unittest.TestCase):
    def test_ratio_follows_sputnik_formula(self):
        self.assertEqual(c3.to_weight([1, 2], 5), 3)
        self.assertEqual(c3.to_weight([55, 100], 4), 3)
        self.assertEqual(c3.to_weight([2, 5], 5), 3)
        self.assertEqual(c3.to_weight([1, 1], 5), 5)
        self.assertEqual(c3.to_weight("3", 5), 3)

    def test_dao_threshold_ignores_roles_that_cannot_approve(self):
        policy = {"default_vote_policy": {"threshold": [1, 2]}, "roles": [
            {"name": "all", "kind": "Everyone", "permissions": ["*:AddProposal"], "vote_policy": {}},
            {"name": "council", "kind": {"Group": ["a", "b", "c", "d", "e"]}, "permissions": ["*:VoteApprove"],
             "vote_policy": {"call": {"threshold": "4"}}}]}
        self.assertEqual(c3.dao_threshold(policy, "call"), (4, 5, "council"))
        self.assertEqual(c3.dao_threshold(policy, "policy"), (3, 5, "council"))


class Verdicts(unittest.TestCase):
    def test_c3a_fails_when_intents_has_one_signer_path(self):
        v = c3.claim_verdicts([row("near-intents", 10, 1, False), row("x", 90, 3, True)])
        self.assertEqual((v["C3a"], v["C3b"], v["C3"]), ("fails", "holds", "fails"))

    def test_c3a_fails_above_30_percent_of_assessed_tvl(self):
        v = c3.claim_verdicts([row("near-intents", 60, 3, False), row("x", 40, 1, True)])
        self.assertEqual(v["C3a"], "fails")

    def test_holds_only_when_both_hold(self):
        v = c3.claim_verdicts([row("near-intents", 50, 3, False), row("x", 30, 3, True), row("y", 20, 2, False)])
        self.assertEqual((v["C3a"], v["C3b"], v["C3"]), ("holds", "holds", "holds"))

    def test_c3b_ignores_intents_and_needs_more_than_half(self):
        v = c3.claim_verdicts([row("near-intents", 50, 3, True), row("x", 50, 3, True), row("y", 50, 3, False)])
        self.assertEqual(v["C3b"], "fails")

    def test_unreadable_majority_is_cant_tell(self):
        v = c3.claim_verdicts([row("near-intents", 10, 3, False), row("x", 90, None, None, readable=False)])
        self.assertEqual((v["C3a"], v["C3b"]), ("can't tell", "can't tell"))


if __name__ == "__main__":
    unittest.main()
