# InsightApp/tests/test_outlier_detection.py
from unittest.mock import patch, MagicMock
from django.test import TestCase
from services.outlier_detection import (
    enrich_with_flags,
    build_baselines,
    flag_outliers,
    OUTLIER_THRESHOLD,
    MIN_BASELINE_ENTRIES,
    BASELINE_MONTHS,
)
from services.insight_query import COLUMNS


# ── shared fixtures ────────────────────────────────────────────────────────────

_ROW_JOAO_CLIENTEB = (
    "20261001", "08:00", "17:00", 42, "João Silva",
    "ClienteB", "Desenvolvimento", "CC-01", "", "",
)

_BASELINE_ABOVE = {
    42: {"total": 100, "clients": {"ClienteA": 0.92, "ClienteB": 0.08},
         "activities": {"Desenvolvimento": 1.0}}
}
_BASELINE_BELOW = {
    42: {"total": 100, "clients": {"ClienteA": 0.98, "ClienteB": 0.02},
         "activities": {"Desenvolvimento": 1.0}}
}
_BASELINE_THIN = {
    42: {"total": 15, "clients": {"ClienteA": 1.0},
         "activities": {"Desenvolvimento": 1.0}}
}


def _make_mock_conn(fetchall_return):
    mock_cursor = MagicMock()
    mock_cursor.fetchall.return_value = fetchall_return
    mock_conn = MagicMock()
    mock_conn.__enter__ = MagicMock(return_value=mock_conn)
    mock_conn.__exit__ = MagicMock(return_value=False)
    mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
    mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
    return mock_conn, mock_cursor


# ── enrich_with_flags tests ────────────────────────────────────────────────────

class EnrichWithFlagsTests(TestCase):
    def test_client_above_threshold_not_flagged(self):
        result = enrich_with_flags((_ROW_JOAO_CLIENTEB,), COLUMNS, _BASELINE_ABOVE)
        self.assertFalse(result[0]["suspicious"])
        self.assertIsNone(result[0]["reason"])
        self.assertEqual(result[0]["baseline_status"], "ok")

    def test_client_below_threshold_is_flagged(self):
        result = enrich_with_flags((_ROW_JOAO_CLIENTEB,), COLUMNS, _BASELINE_BELOW)
        self.assertTrue(result[0]["suspicious"])
        self.assertIn("ClienteB", result[0]["reason"])
        self.assertIn("2%", result[0]["reason"])
        self.assertIn("João Silva", result[0]["reason"])
        self.assertEqual(result[0]["baseline_status"], "ok")

    def test_thin_baseline_not_flagged(self):
        result = enrich_with_flags((_ROW_JOAO_CLIENTEB,), COLUMNS, _BASELINE_THIN)
        self.assertFalse(result[0]["suspicious"])
        self.assertIsNone(result[0]["reason"])
        self.assertEqual(result[0]["baseline_status"], "insuficiente")

    def test_employee_absent_from_baselines_treated_as_insuficiente(self):
        # Review Focus #1 — cod 99 not in baselines at all
        row = ("20261001", "08:00", "17:00", 99, "Maria Costa",
               "ClienteX", "Suporte", "CC-02", "", "")
        result = enrich_with_flags((row,), COLUMNS, {})
        self.assertFalse(result[0]["suspicious"])
        self.assertEqual(result[0]["baseline_status"], "insuficiente")

    def test_client_never_seen_in_baseline_is_flagged(self):
        # Review Focus #2 — 0.0 frequency must still trigger the flag
        baseline = {42: {"total": 100, "clients": {"ClienteA": 1.0},
                         "activities": {"Desenvolvimento": 1.0}}}
        row = ("20261001", "08:00", "17:00", 42, "João Silva",
               "ClienteNovo", "Desenvolvimento", "CC-01", "", "")
        result = enrich_with_flags((row,), COLUMNS, baseline)
        self.assertTrue(result[0]["suspicious"])
        self.assertIn("ClienteNovo", result[0]["reason"])

    def test_both_client_and_activity_outlier_reasons_joined_with_pipe(self):
        baseline = {42: {"total": 100,
                         "clients": {"ClienteA": 0.98, "ClienteB": 0.02},
                         "activities": {"Desenvolvimento": 0.98, "Auditoria": 0.02}}}
        row = ("20261001", "08:00", "17:00", 42, "João Silva",
               "ClienteB", "Auditoria", "CC-01", "", "")
        result = enrich_with_flags((row,), COLUMNS, baseline)
        self.assertTrue(result[0]["suspicious"])
        self.assertIn(" | ", result[0]["reason"])
        self.assertIn("ClienteB", result[0]["reason"])
        self.assertIn("Auditoria", result[0]["reason"])

    def test_empty_rows_returns_empty_list(self):
        # Review Focus #4
        result = enrich_with_flags((), COLUMNS, {})
        self.assertEqual(result, [])

    def test_original_column_values_preserved(self):
        result = enrich_with_flags((_ROW_JOAO_CLIENTEB,), COLUMNS, _BASELINE_ABOVE)
        self.assertEqual(result[0]["Colaborador"], "João Silva")
        self.assertEqual(result[0]["NomeCliente"], "ClienteB")
        self.assertEqual(result[0]["CodColaborador"], 42)


# ── build_baselines tests ──────────────────────────────────────────────────────

class BuildBaselinesTests(TestCase):
    def test_returns_correct_frequency_distribution(self):
        db_rows = [(42, "ClienteA", "Desenvolvimento", 90),
                   (42, "ClienteB", "Desenvolvimento", 10)]
        mock_conn, _ = _make_mock_conn(db_rows)
        with patch("services.outlier_detection.pymysql.connect", return_value=mock_conn):
            result = build_baselines([42])
        self.assertEqual(result[42]["total"], 100)
        self.assertAlmostEqual(result[42]["clients"]["ClienteA"], 0.90)
        self.assertAlmostEqual(result[42]["clients"]["ClienteB"], 0.10)

    def test_empty_list_returns_empty_dict_without_db_call(self):
        # Review Focus #4 — no DB call needed
        result = build_baselines([])
        self.assertEqual(result, {})

    def test_employee_with_no_history_absent_from_result(self):
        # Review Focus #1 — DB returns no rows for this employee
        mock_conn, _ = _make_mock_conn([])
        with patch("services.outlier_detection.pymysql.connect", return_value=mock_conn):
            result = build_baselines([42])
        self.assertNotIn(42, result)


# ── flag_outliers tests ────────────────────────────────────────────────────────

class FlagOutliersTests(TestCase):
    def test_empty_rows_returns_empty_list(self):
        result = flag_outliers((), COLUMNS)
        self.assertEqual(result, [])

    def test_integrates_build_baselines_and_enrich(self):
        db_rows = [(42, "ClienteA", "Desenvolvimento", 98),
                   (42, "ClienteB", "Desenvolvimento",  2)]
        mock_conn, _ = _make_mock_conn(db_rows)
        insight_rows = (
            ("20261001", "08:00", "17:00", 42, "João Silva",
             "ClienteB", "Desenvolvimento", "CC-01", "", ""),
        )
        with patch("services.outlier_detection.pymysql.connect", return_value=mock_conn):
            result = flag_outliers(insight_rows, COLUMNS)
        self.assertEqual(len(result), 1)
        self.assertTrue(result[0]["suspicious"])
        self.assertIn("ClienteB", result[0]["reason"])
