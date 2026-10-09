# InsightApp/tests/test_insight_query.py
from unittest.mock import patch, MagicMock
from django.test import TestCase
from services.insight_query import query_insight_entries, COLUMNS


def _make_mock_conn(fetchall_return):
    """Returns (mock_conn, mock_cursor) wired for PyMySQL context-manager usage."""
    mock_cursor = MagicMock()
    mock_cursor.fetchall.return_value = fetchall_return
    mock_conn = MagicMock()
    mock_conn.__enter__ = MagicMock(return_value=mock_conn)
    mock_conn.__exit__ = MagicMock(return_value=False)
    mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
    mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
    return mock_conn, mock_cursor


class InsightQueryTests(TestCase):
    def test_returns_columns_constant_and_rows(self):
        mock_rows = (
            ("20260101", "08:00", "17:00", 42, "João Silva",
             "ClienteA", "Desenvolvimento", "CC-01", "", ""),
        )
        mock_conn, _ = _make_mock_conn(mock_rows)
        with patch("services.insight_query.pymysql.connect", return_value=mock_conn):
            rows, columns = query_insight_entries("20260101", "20261231")
        self.assertEqual(columns, COLUMNS)
        self.assertEqual(rows, mock_rows)

    def test_returns_empty_tuple_when_no_data(self):
        mock_conn, _ = _make_mock_conn(())
        with patch("services.insight_query.pymysql.connect", return_value=mock_conn):
            rows, columns = query_insight_entries("20260101", "20260101")
        self.assertEqual(rows, ())
        self.assertEqual(columns, COLUMNS)

    def test_no_optional_filters_sends_only_two_params(self):
        # Review Focus #3 — no LIKE clause when all optionals are None
        mock_conn, mock_cursor = _make_mock_conn(())
        with patch("services.insight_query.pymysql.connect", return_value=mock_conn):
            query_insight_entries("20260101", "20261231")
        executed_params = mock_cursor.execute.call_args[0][1]
        executed_sql = mock_cursor.execute.call_args[0][0]
        self.assertEqual(len(executed_params), 2)
        self.assertNotIn("LIKE", executed_sql)

    def test_optional_nomecolaborador_adds_like_clause(self):
        mock_conn, mock_cursor = _make_mock_conn(())
        with patch("services.insight_query.pymysql.connect", return_value=mock_conn):
            query_insight_entries("20260101", "20261231", nomeColaborador="João")
        executed_sql = mock_cursor.execute.call_args[0][0]
        executed_params = mock_cursor.execute.call_args[0][1]
        self.assertIn("pessoa.nome LIKE", executed_sql)
        self.assertIn("%João%", executed_params)
