from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from unittest.mock import patch, MagicMock
import pandas as pd
from datetime import datetime

from services.utils import passarParaDecimal
from services.defToExcel import transformaParaDf


# ---------------------------------------------------------------------------
# utils.passarParaDecimal
# ---------------------------------------------------------------------------

class PassarParaDecimalTests(TestCase):
    def test_single_digit_hour(self):
        self.assertAlmostEqual(passarParaDecimal("1:30"), 1.5)

    def test_two_digit_hour(self):
        self.assertAlmostEqual(passarParaDecimal("10:30"), 10.5)

    def test_three_digit_hour(self):
        self.assertAlmostEqual(passarParaDecimal("100:00"), 100.0)

    def test_zero_minutes(self):
        self.assertEqual(passarParaDecimal("8:00"), 8.0)

    def test_full_hour(self):
        self.assertAlmostEqual(passarParaDecimal("2:60"), 3.0)


# ---------------------------------------------------------------------------
# transformaParaDf
# ---------------------------------------------------------------------------

class TransformaParaDfTests(TestCase):
    def _make_row(self, data="20230101", hora_inicio="0800", hora_fim="1700",
                  obs1="task", obs2="", colaborador="Alice"):
        return (data, hora_inicio, hora_fim, 1, obs1, obs2,
                colaborador, "Dev", "ClienteX", "CC001")

    def test_returns_dataframe(self):
        rows = (self._make_row(),)
        columns = ("Data", "HoraInicio", "HoraFim", "CodAtividade",
                   "Observacao1", "Observacao2", "Colaborador",
                   "DescricaoAtividade", "NomeCliente", "CentroCusto")
        df = transformaParaDf(rows, columns)
        self.assertIsInstance(df, pd.DataFrame)

    def test_qtde_horas_column_created(self):
        rows = (self._make_row(),)
        columns = ("Data", "HoraInicio", "HoraFim", "CodAtividade",
                   "Observacao1", "Observacao2", "Colaborador",
                   "DescricaoAtividade", "NomeCliente", "CentroCusto")
        df = transformaParaDf(rows, columns)
        self.assertIn("Qtde Horas", df.columns)

    def test_empty_rows_returns_empty_df(self):
        columns = ("Data", "HoraInicio", "HoraFim", "CodAtividade",
                   "Observacao1", "Observacao2", "Colaborador",
                   "DescricaoAtividade", "NomeCliente", "CentroCusto")
        df = transformaParaDf((), columns)
        self.assertTrue(df.empty)

    def test_descricao_combines_obs1_and_obs2(self):
        rows = (self._make_row(obs1="task", obs2="extra"),)
        columns = ("Data", "HoraInicio", "HoraFim", "CodAtividade",
                   "Observacao1", "Observacao2", "Colaborador",
                   "DescricaoAtividade", "NomeCliente", "CentroCusto")
        df = transformaParaDf(rows, columns)
        self.assertEqual(df.iloc[0]["Descricao"], "task + extra")

    def test_descricao_obs2_empty_uses_only_obs1(self):
        rows = (self._make_row(obs1="only task", obs2=""),)
        columns = ("Data", "HoraInicio", "HoraFim", "CodAtividade",
                   "Observacao1", "Observacao2", "Colaborador",
                   "DescricaoAtividade", "NomeCliente", "CentroCusto")
        df = transformaParaDf(rows, columns)
        self.assertEqual(df.iloc[0]["Descricao"], "only task")


# ---------------------------------------------------------------------------
# Views — authentication
# ---------------------------------------------------------------------------

class LoginViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="testuser", password="pass1234")

    def test_login_page_renders(self):
        response = self.client.get(reverse("login"))
        self.assertEqual(response.status_code, 200)

    def test_valid_login_redirects_to_main(self):
        response = self.client.post(
            reverse("login"), {"username": "testuser", "password": "pass1234"}
        )
        self.assertRedirects(response, reverse("main"))

    def test_invalid_login_shows_error(self):
        response = self.client.post(
            reverse("login"), {"username": "testuser", "password": "wrong"}
        )
        self.assertEqual(response.status_code, 200)
        messages = list(response.wsgi_request._messages)
        self.assertTrue(any("erro" in str(m).lower() for m in messages))

    def test_logout_redirects_to_login(self):
        self.client.login(username="testuser", password="pass1234")
        response = self.client.get(reverse("logout"))
        self.assertRedirects(response, reverse("login"))


class MainViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="testuser", password="pass1234")
        self.client.login(username="testuser", password="pass1234")

    def test_unauthenticated_user_redirected(self):
        self.client.logout()
        response = self.client.get(reverse("main"))
        self.assertEqual(response.status_code, 302)

    def test_authenticated_user_sees_form(self):
        response = self.client.get(reverse("main"))
        self.assertEqual(response.status_code, 200)
        self.assertIn("form", response.context)

    @patch("AtividadeApp.views.exportar_excel")
    def test_valid_post_triggers_excel_generation(self, mock_excel):
        mock_wb = MagicMock()
        mock_excel.return_value = mock_wb
        response = self.client.post(reverse("main"), {
            "dataInicio": "2023-01-01",
            "dataFim": "2023-01-31",
            "maxCodColaborador": 99,
            "maxCliente": "ZZZZZZZZZZZZZZZ",
            "maxAtividade": "ZZZZZZZZZZZZZZZ",
            "maxCentroCusto": "ZZZZZZZZZZZZZZZ",
        })
        mock_excel.assert_called_once()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/ms-excel")


# ---------------------------------------------------------------------------
# API view
# ---------------------------------------------------------------------------

class ApiGetDataViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        user = User.objects.create_user(username="apiuser", password="pass1234")
        self.client.login(username="apiuser", password="pass1234")

    @patch("AtividadeApp.views.exportar_json")
    def test_returns_json(self, mock_dict):
        mock_dict.return_value = {"atividades": []}
        response = self.client.get(reverse("getData"), {
            "dataInicio": "20230101", "dataFim": "20230131"
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")

    @patch("AtividadeApp.views.exportar_json")
    def test_defaults_applied_when_params_missing(self, mock_dict):
        mock_dict.return_value = {}
        self.client.get(reverse("getData"))
        mock_dict.assert_called_once()
