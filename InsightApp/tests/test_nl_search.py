# InsightApp/tests/test_nl_search.py
from django.test import TestCase
from services.nl_search import nl_to_filters


class NlSearchTests(TestCase):
    def test_stub_returns_none_for_any_text(self):
        result = nl_to_filters("mostre os lançamentos de João em outubro")
        self.assertIsNone(result)

    def test_stub_returns_none_for_empty_string(self):
        result = nl_to_filters("")
        self.assertIsNone(result)
