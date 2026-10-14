import unittest
from insights.core import analyze, classify, export_csv, load_csv, validate


class InsightTests(unittest.TestCase):
    def test_same_user_duplicate_removed(self):
        rows = [{"text":"响应慢","rating":1,"user_id":"u"}] * 2
        self.assertEqual(analyze(rows)["duplicate_n"], 1)

    def test_different_users_preserved(self):
        rows = [{"text":"响应慢","rating":1,"user_id":u} for u in ["a", "b"]]
        self.assertEqual(analyze(rows)["backlog"][0]["reach"], 2)

    def test_invalid_rating(self):
        with self.assertRaises(ValueError):
            validate([{"text":"测试","rating":9}])

    def test_empty_text_skipped(self):
        self.assertEqual(analyze([{"text":" "}])["valid_n"], 0)

    def test_unknown_requires_review(self):
        self.assertEqual(classify("不错加油")["label"], "待人工分类")

    def test_privacy_priority(self):
        self.assertEqual(classify("界面很慢而且泄露隐私")["label"], "隐私安全")

    def test_override_and_audit(self):
        report = analyze([{"id":"a","text":"比较慢","rating":2}], {"a":"交互体验"})
        self.assertEqual(report["feedback"][0]["method"], "人工复核")
        self.assertFalse(report["feedback"][0]["review_required"])

    def test_rice_calculation(self):
        rows = [{"id":"1","user_id":"a","text":"超时","rating":1}, {"id":"2","user_id":"b","text":"响应慢","rating":2}]
        report = analyze(rows, estimates={"响应性能":{"impact":3,"confidence":.8,"effort":2}})
        self.assertEqual(report["backlog"][0]["rice"], 2.4)

    def test_zero_effort_rejected(self):
        with self.assertRaises(ValueError):
            analyze([{"text":"超时"}], estimates={"响应性能":{"effort":0}})

    def test_csv_header_validation(self):
        with self.assertRaises(ValueError):
            load_csv("a,b\n1,2")

    def test_csv_formula_escaped(self):
        report = analyze([{"id":"=WEBSERVICE(a)","text":"超时"}])
        self.assertIn("'=WEBSERVICE", export_csv(report))

    def test_duplicate_ids_rejected(self):
        with self.assertRaises(ValueError):
            validate([{"id":"a","text":"慢"},{"id":"a","text":"超时"}])


if __name__ == "__main__":
    unittest.main()
