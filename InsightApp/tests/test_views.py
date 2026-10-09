# InsightApp/tests/test_views.py
from unittest.mock import patch
from django.test import TestCase, Client
from django.contrib.auth.models import User
from services.insight_query import COLUMNS


class InsightViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="testuser", password="testpass123")

    def test_unauthenticated_get_redirects_to_login(self):
        response = self.client.get("/insights/")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/auth/login/", response["Location"])

    def test_authenticated_get_returns_200_with_form(self):
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get("/insights/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Busca por linguagem natural")
        self.assertContains(response, "Data Início")

    def test_post_valid_dates_returns_200(self):
        self.client.login(username="testuser", password="testpass123")
        with patch("InsightApp.views.query_insight_entries") as mock_q, \
             patch("InsightApp.views.flag_outliers", return_value=[]):
            mock_q.return_value = ((), COLUMNS)
            response = self.client.post("/insights/", {
                "dataInicio": "2026-01-01",
                "dataFim": "2026-10-01",
            })
        self.assertEqual(response.status_code, 200)

    def test_nl_stub_returning_none_is_silently_ignored(self):
        self.client.login(username="testuser", password="testpass123")
        with patch("InsightApp.views.query_insight_entries") as mock_q, \
             patch("InsightApp.views.flag_outliers", return_value=[]), \
             patch("InsightApp.views.nl_to_filters", return_value=None):
            mock_q.return_value = ((), COLUMNS)
            response = self.client.post("/insights/", {
                "dataInicio": "2026-01-01",
                "dataFim": "2026-10-01",
                "nl_query": "mostre os suspeitos de outubro",
            })
        self.assertEqual(response.status_code, 200)

    def test_summary_shows_zero_suspicious_when_all_thin_baseline(self):
        # Review Focus #5
        self.client.login(username="testuser", password="testpass123")
        thin_entries = [{
            "Data": "20261001", "HoraInicio": "08:00", "HoraFim": "17:00",
            "CodColaborador": 1, "Colaborador": "João Silva",
            "NomeCliente": "ClienteA", "DescricaoAtividade": "Dev",
            "CentroCusto": "CC-01", "Observacao1": "", "Observacao2": "",
            "suspicious": False, "reason": None, "baseline_status": "insuficiente",
        }]
        with patch("InsightApp.views.query_insight_entries") as mock_q, \
             patch("InsightApp.views.flag_outliers", return_value=thin_entries):
            mock_q.return_value = (
                (("20261001", "08:00", "17:00", 1, "João", "ClienteA", "Dev", "CC-01", "", ""),),
                COLUMNS,
            )
            response = self.client.post("/insights/", {
                "dataInicio": "2026-10-01",
                "dataFim": "2026-10-31",
            })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Suspeitos: 0")
        self.assertContains(response, "Sem baseline: 1")

    def test_thin_baseline_entry_renders_warning_tooltip(self):
        self.client.login(username="testuser", password="testpass123")
        thin_entries = [{
            "Data": "20261001", "HoraInicio": "08:00", "HoraFim": "17:00",
            "CodColaborador": 1, "Colaborador": "João Silva",
            "NomeCliente": "ClienteA", "DescricaoAtividade": "Dev",
            "CentroCusto": "CC-01", "Observacao1": "", "Observacao2": "",
            "suspicious": False, "reason": None, "baseline_status": "insuficiente",
        }]
        with patch("InsightApp.views.query_insight_entries") as mock_q, \
             patch("InsightApp.views.flag_outliers", return_value=thin_entries):
            mock_q.return_value = (
                (("20261001", "08:00", "17:00", 1, "João", "ClienteA", "Dev", "CC-01", "", ""),),
                COLUMNS,
            )
            response = self.client.post("/insights/", {
                "dataInicio": "2026-10-01",
                "dataFim": "2026-10-31",
            })
        self.assertContains(
            response,
            'title="Baseline insuficiente (menos de 20 registros nos últimos 12 meses)"',
        )

    def test_suspicious_entry_renders_red_flag_and_css_class(self):
        self.client.login(username="testuser", password="testpass123")
        suspicious_entries = [{
            "Data": "20261001", "HoraInicio": "08:00", "HoraFim": "17:00",
            "CodColaborador": 1, "Colaborador": "João Silva",
            "NomeCliente": "ClienteB", "DescricaoAtividade": "Dev",
            "CentroCusto": "CC-01", "Observacao1": "", "Observacao2": "",
            "suspicious": True,
            "reason": "Cliente 'ClienteB' representa apenas 2% do histórico de João Silva (últimos 12 meses)",
            "baseline_status": "ok",
        }]
        with patch("InsightApp.views.query_insight_entries") as mock_q, \
             patch("InsightApp.views.flag_outliers", return_value=suspicious_entries):
            mock_q.return_value = (
                (("20261001", "08:00", "17:00", 1, "João", "ClienteB", "Dev", "CC-01", "", ""),),
                COLUMNS,
            )
            response = self.client.post("/insights/", {
                "dataInicio": "2026-10-01",
                "dataFim": "2026-10-31",
            })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "🔴")
        self.assertContains(response, "entry-suspicious")
