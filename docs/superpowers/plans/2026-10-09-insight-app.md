# InsightApp Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a `/insights/` screen that renders lançamentos as an HTML table and highlights statistically suspicious entries per employee using 12-month historical baselines.

**Architecture:** New `InsightApp/` Django app in the existing project. Three new service modules (`nl_search`, `insight_query`, `outlier_detection`) with clean interfaces. The view orchestrates all three. No new Django models; all data comes directly from the `back_office` MySQL DB.

**Tech Stack:** Django 6.1, PyMySQL 1.2.0, Python 3.11+. No new pip packages.

**Spec:** `docs/superpowers/specs/2026-10-09-insight-app-design.md`

## Global Constraints

- Python 3.11+ — use `str | None` union types (not `Optional[str]`)
- No new pip packages — only what is already in `requirements.txt`
- DB credentials via `load_dotenv()` then `os.environ["DB_HOST"]`, `os.environ["DB_USER"]`, `os.environ["DB_PASSWORD"]`, `os.environ.get("DB_NAME", "back_office")`
- All user-visible strings in Portuguese, consistent with the existing app
- `@login_required` redirects to `"login"` named URL (`/auth/login/`) — `LOGIN_URL = "login"` is already in `settings.py`
- Run tests with `python manage.py test InsightApp`
- Outlier constants at top of `outlier_detection.py`: `OUTLIER_THRESHOLD = 0.05`, `MIN_BASELINE_ENTRIES = 20`, `BASELINE_MONTHS = 12`
- `base.html` has no Django template blocks — `insights.html` must include `AtividadeApp/partials/_head.html` directly and build the full page

## Review Focus

1. **Employee with no history at all** — `cod_colaborador` appears in current results but has zero rows in the last 12 months; `build_baselines` returns `{}` for that code; `enrich_with_flags` calls `baselines.get(cod_colab)` which returns `None`; must set `baseline_status="insuficiente"`, not crash. → Test in Task 3.

2. **Client/activity never seen in baseline (0 occurrences)** — `baseline["clients"].get(cliente, 0.0)` returns `0.0`; `0.0 < OUTLIER_THRESHOLD` is `True`; entry must be flagged. → Test in Task 3.

3. **All optional filters are `None`** — `query_insight_entries("20260101", "20261231")` with no optional args must build only two date `WHERE` clauses and not crash. → Test in Task 2.

4. **Empty rows from query** — `flag_outliers((), COLUMNS)` receives empty tuple; the set comprehension iterates nothing; `build_baselines([])` must return `{}`; overall must return `[]`. → Test in Task 3.

5. **All employees have thin baseline** — every entry gets `suspicious=False, baseline_status="insuficiente"`; `_build_summary` must produce `suspicious=0, thin_baseline=N`; template must render `"Suspeitos: 0"`. → Test in Task 4.

---

## File Map

| Path | Action | Responsibility |
|------|--------|----------------|
| `services/nl_search.py` | Create | Stub — `nl_to_filters(text) → None` |
| `services/insight_query.py` | Create | MySQL query: entries by date range + optional filters |
| `services/outlier_detection.py` | Create | `build_baselines`, `enrich_with_flags`, `flag_outliers` |
| `InsightApp/__init__.py` | Create | Empty package marker |
| `InsightApp/apps.py` | Create | `InsightAppConfig` |
| `InsightApp/forms.py` | Create | `InsightFilterForm` |
| `InsightApp/views.py` | Create | `insights_view` — orchestrates query + flagging + NL seam |
| `InsightApp/urls.py` | Create | `path("insights/", ...)` |
| `InsightApp/templates/InsightApp/insights.html` | Create | Full-page template, 3-zone layout |
| `InsightApp/tests/__init__.py` | Create | Empty — makes tests a package |
| `InsightApp/tests/test_nl_search.py` | Create | Tests for `nl_to_filters` stub |
| `InsightApp/tests/test_insight_query.py` | Create | Tests for `query_insight_entries` |
| `InsightApp/tests/test_outlier_detection.py` | Create | Tests for `enrich_with_flags`, `build_baselines`, `flag_outliers` |
| `InsightApp/tests/test_views.py` | Create | Django test-client tests for `insights_view` |
| `backOfficeProject/settings.py` | Modify | Add `"InsightApp"` to `INSTALLED_APPS` |
| `backOfficeProject/urls.py` | Modify | Add `include("InsightApp.urls")` |

---

## Task 1: NL Search Stub

**Files:**
- Create: `services/nl_search.py`
- Create: `InsightApp/__init__.py`, `InsightApp/tests/__init__.py`
- Create: `InsightApp/tests/test_nl_search.py`

**Interfaces:**
- Produces: `nl_to_filters(text: str) -> dict | None` — imported by `insights_view` in Task 4

- [ ] **Step 1: Create directories and empty init files**

```bash
mkdir -p InsightApp/tests
type nul > InsightApp/__init__.py
type nul > InsightApp/tests/__init__.py
```

- [ ] **Step 2: Write the failing test**

```python
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
```

- [ ] **Step 3: Run test and verify it fails**

```bash
python manage.py test InsightApp.tests.test_nl_search
```
Expected: `ModuleNotFoundError: No module named 'services.nl_search'`

- [ ] **Step 4: Create `services/nl_search.py`**

```python
# services/nl_search.py


def nl_to_filters(text: str) -> dict | None:
    """
    Translate a natural-language query into filter parameters.

    TODO: implement with an LLM (e.g. Claude API).
    Return a dict with any subset of keys:
        dataInicio, dataFim, nomeColaborador, nomeCliente, atividade, centroCusto
    Return None if text cannot be parsed — the view ignores NL input gracefully.

    Example return value:
        {"nomeColaborador": "João", "nomeCliente": "Sinosbyte", "dataInicio": "20260101"}
    """
    return None  # stub
```

- [ ] **Step 5: Run test and verify it passes**

```bash
python manage.py test InsightApp.tests.test_nl_search
```
Expected: `OK (2 tests)`

- [ ] **Step 6: Commit**

```bash
git add services/nl_search.py InsightApp/__init__.py InsightApp/tests/__init__.py InsightApp/tests/test_nl_search.py
git commit -m "feat: add nl_search stub and InsightApp test scaffolding"
```

---

## Task 2: Insight Query Service

**Files:**
- Create: `services/insight_query.py`
- Create: `InsightApp/tests/test_insight_query.py`

**Interfaces:**
- Produces:
  - `COLUMNS: tuple[str, ...]` — module-level constant; imported by Task 3 tests and Task 4 view
  - `query_insight_entries(dataInicio: str, dataFim: str, nomeColaborador: str | None = None, nomeCliente: str | None = None, atividade: str | None = None, centroCusto: str | None = None) -> tuple[tuple, tuple]`

- [ ] **Step 1: Write failing tests**

```python
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
```

- [ ] **Step 2: Run tests and verify they fail**

```bash
python manage.py test InsightApp.tests.test_insight_query
```
Expected: `ModuleNotFoundError: No module named 'services.insight_query'`

- [ ] **Step 3: Create `services/insight_query.py`**

```python
# services/insight_query.py
import os
import pymysql
from dotenv import load_dotenv

load_dotenv()

COLUMNS: tuple[str, ...] = (
    "Data",
    "HoraInicio",
    "HoraFim",
    "CodColaborador",
    "Colaborador",
    "NomeCliente",
    "DescricaoAtividade",
    "CentroCusto",
    "Observacao1",
    "Observacao2",
)


def query_insight_entries(
    dataInicio: str,
    dataFim: str,
    nomeColaborador: str | None = None,
    nomeCliente: str | None = None,
    atividade: str | None = None,
    centroCusto: str | None = None,
) -> tuple[tuple, tuple]:
    """
    Fetch lançamento entries for the given date range with optional name filters.
    Returns (rows, COLUMNS) — same contract as selectDataFromDatabase in selectData.py.
    """
    where_clauses: list[str] = [
        "rat.data_atividade_s >= %s",
        "rat.data_atividade_s <= %s",
    ]
    params: list = [dataInicio, dataFim]

    if nomeColaborador:
        where_clauses.append("pessoa.nome LIKE %s")
        params.append(f"%{nomeColaborador}%")
    if nomeCliente:
        where_clauses.append("em.nome_abrev LIKE %s")
        params.append(f"%{nomeCliente}%")
    if atividade:
        where_clauses.append("ativ.desc_atividade LIKE %s")
        params.append(f"%{atividade}%")
    if centroCusto:
        where_clauses.append("ncc.codigo LIKE %s")
        params.append(f"%{centroCusto}%")

    where_sql = " AND ".join(where_clauses)

    query = f"""
        SELECT
            rat.data_atividade_s   AS Data,
            rat.hora_inicio_s      AS HoraInicio,
            rat.hora_final_s       AS HoraFim,
            colab.cod_colaborador  AS CodColaborador,
            pessoa.nome            AS Colaborador,
            em.nome_abrev          AS NomeCliente,
            ativ.desc_atividade    AS DescricaoAtividade,
            ncc.descricao          AS CentroCusto,
            rat.observacao1        AS Observacao1,
            rat.observacao2        AS Observacao2
        FROM ra_atividade_trabalho rat
        INNER JOIN atividade ativ       ON rat.atividade_cod_atividade = ativ.cod_atividade
        INNER JOIN colaboradores colab  ON rat.cod_colaborador = colab.cod_colaborador
        INNER JOIN pessoa               ON colab.cod_pessoa = pessoa.cod_pessoa
        INNER JOIN new_centro_custo ncc ON ativ.centroCusto_id = ncc.id
        INNER JOIN emitente em          ON rat.cod_emitente = em.cod_emitente
        WHERE {where_sql}
        ORDER BY rat.data_atividade_s DESC, pessoa.nome
    """

    connection = pymysql.connect(
        host=os.environ["DB_HOST"],
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        database=os.environ.get("DB_NAME", "back_office"),
    )
    with connection:
        with connection.cursor() as cursor:
            cursor.execute(query, params)
            rows: tuple = cursor.fetchall()

    return rows, COLUMNS
```

- [ ] **Step 4: Run tests and verify they pass**

```bash
python manage.py test InsightApp.tests.test_insight_query
```
Expected: `OK (4 tests)`

- [ ] **Step 5: Commit**

```bash
git add services/insight_query.py InsightApp/tests/test_insight_query.py
git commit -m "feat: add insight_query service"
```

---

## Task 3: Outlier Detection Service

**Files:**
- Create: `services/outlier_detection.py`
- Create: `InsightApp/tests/test_outlier_detection.py`

**Interfaces:**
- Consumes: `COLUMNS` from `services.insight_query` (used in tests to get the column tuple)
- Produces:
  - `OUTLIER_THRESHOLD: float`, `MIN_BASELINE_ENTRIES: int`, `BASELINE_MONTHS: int`
  - `build_baselines(cod_colaborador_list: list[int]) -> dict[int, dict]` where each value has keys `total: int`, `clients: dict[str, float]`, `activities: dict[str, float]`
  - `enrich_with_flags(rows: tuple, columns: tuple, baselines: dict) -> list[dict]` — each dict contains all original column values plus `suspicious: bool`, `reason: str | None`, `baseline_status: str` (`"ok"` or `"insuficiente"`)
  - `flag_outliers(rows: tuple, columns: tuple) -> list[dict]` — convenience wrapper

- [ ] **Step 1: Write failing tests for `enrich_with_flags` (pure logic, no DB)**

```python
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
```

- [ ] **Step 2: Run tests and verify they fail**

```bash
python manage.py test InsightApp.tests.test_outlier_detection
```
Expected: `ModuleNotFoundError: No module named 'services.outlier_detection'`

- [ ] **Step 3: Create `services/outlier_detection.py`**

```python
# services/outlier_detection.py
import os
from datetime import datetime, timedelta
import pymysql
from dotenv import load_dotenv

load_dotenv()

OUTLIER_THRESHOLD: float = 0.05
MIN_BASELINE_ENTRIES: int = 20
BASELINE_MONTHS: int = 12


def build_baselines(cod_colaborador_list: list[int]) -> dict[int, dict]:
    """
    Query the last BASELINE_MONTHS months of history for the given employees.
    Returns dict keyed by cod_colaborador:
        {<cod>: {"total": int, "clients": {name: freq}, "activities": {name: freq}}}
    Employees with no history rows are absent from the returned dict.
    """
    if not cod_colaborador_list:
        return {}

    cutoff = (datetime.now() - timedelta(days=BASELINE_MONTHS * 30)).strftime("%Y%m%d")
    today = datetime.now().strftime("%Y%m%d")
    placeholders = ",".join(["%s"] * len(cod_colaborador_list))

    query = f"""
        SELECT
            colab.cod_colaborador,
            em.nome_abrev        AS cliente,
            ativ.desc_atividade  AS atividade,
            COUNT(*)             AS qtd
        FROM ra_atividade_trabalho rat
        INNER JOIN atividade ativ       ON rat.atividade_cod_atividade = ativ.cod_atividade
        INNER JOIN colaboradores colab  ON rat.cod_colaborador = colab.cod_colaborador
        INNER JOIN emitente em          ON rat.cod_emitente = em.cod_emitente
        WHERE colab.cod_colaborador IN ({placeholders})
          AND rat.data_atividade_s >= %s
          AND rat.data_atividade_s <= %s
        GROUP BY colab.cod_colaborador, em.nome_abrev, ativ.desc_atividade
    """
    params = cod_colaborador_list + [cutoff, today]

    connection = pymysql.connect(
        host=os.environ["DB_HOST"],
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        database=os.environ.get("DB_NAME", "back_office"),
    )
    with connection:
        with connection.cursor() as cursor:
            cursor.execute(query, params)
            rows = cursor.fetchall()

    raw: dict[int, dict] = {}
    for cod_colab, cliente, atividade, qtd in rows:
        if cod_colab not in raw:
            raw[cod_colab] = {"total": 0, "clients": {}, "activities": {}}
        raw[cod_colab]["total"] += qtd
        raw[cod_colab]["clients"][cliente] = raw[cod_colab]["clients"].get(cliente, 0) + qtd
        raw[cod_colab]["activities"][atividade] = (
            raw[cod_colab]["activities"].get(atividade, 0) + qtd
        )

    baselines: dict[int, dict] = {}
    for cod_colab, data in raw.items():
        total = data["total"]
        baselines[cod_colab] = {
            "total": total,
            "clients":    {k: v / total for k, v in data["clients"].items()},
            "activities": {k: v / total for k, v in data["activities"].items()},
        }
    return baselines


def enrich_with_flags(
    rows: tuple, columns: tuple, baselines: dict
) -> list[dict]:
    """
    For each entry row, check client/activity frequency against the employee baseline.
    Returns list of dicts with all original column values plus:
        suspicious: bool
        reason: str | None  (Portuguese; multiple reasons joined with " | ")
        baseline_status: "ok" | "insuficiente"
    """
    col_idx = {name: i for i, name in enumerate(columns)}
    result: list[dict] = []

    for row in rows:
        entry = {col: row[i] for col, i in col_idx.items()}
        cod_colab = entry["CodColaborador"]
        baseline = baselines.get(cod_colab)

        if baseline is None or baseline["total"] < MIN_BASELINE_ENTRIES:
            entry["suspicious"] = False
            entry["reason"] = None
            entry["baseline_status"] = "insuficiente"
            result.append(entry)
            continue

        reasons: list[str] = []
        colaborador = entry["Colaborador"]
        cliente = entry["NomeCliente"]
        atividade = entry["DescricaoAtividade"]

        client_freq = baseline["clients"].get(cliente, 0.0)
        if client_freq < OUTLIER_THRESHOLD:
            pct = round(client_freq * 100)
            reasons.append(
                f"Cliente '{cliente}' representa apenas {pct}% do histórico de "
                f"{colaborador} (últimos {BASELINE_MONTHS} meses)"
            )

        activity_freq = baseline["activities"].get(atividade, 0.0)
        if activity_freq < OUTLIER_THRESHOLD:
            pct = round(activity_freq * 100)
            reasons.append(
                f"Atividade '{atividade}' representa apenas {pct}% do histórico de "
                f"{colaborador} (últimos {BASELINE_MONTHS} meses)"
            )

        entry["suspicious"] = bool(reasons)
        entry["reason"] = " | ".join(reasons) if reasons else None
        entry["baseline_status"] = "ok"
        result.append(entry)

    return result


def flag_outliers(rows: tuple, columns: tuple) -> list[dict]:
    """
    Convenience: builds baselines for all employees in rows, then enriches.
    Returns [] immediately if rows is empty.
    """
    if not rows:
        return []
    col_idx = {name: i for i, name in enumerate(columns)}
    cod_colabs = list({row[col_idx["CodColaborador"]] for row in rows})
    baselines = build_baselines(cod_colabs)
    return enrich_with_flags(rows, columns, baselines)
```

- [ ] **Step 4: Run tests and verify they pass**

```bash
python manage.py test InsightApp.tests.test_outlier_detection
```
Expected: `OK (11 tests)`

- [ ] **Step 5: Commit**

```bash
git add services/outlier_detection.py InsightApp/tests/test_outlier_detection.py
git commit -m "feat: add outlier_detection service"
```

---

## Task 4: InsightApp Django App, View, and Template

**Files:**
- Create: `InsightApp/apps.py`, `InsightApp/forms.py`, `InsightApp/views.py`, `InsightApp/urls.py`
- Create: `InsightApp/templates/InsightApp/insights.html`
- Create: `InsightApp/tests/test_views.py`
- Modify: `backOfficeProject/settings.py` (line 46), `backOfficeProject/urls.py`

**Interfaces:**
- Consumes:
  - `query_insight_entries(**params)` from `services.insight_query`
  - `flag_outliers(rows, columns)` from `services.outlier_detection`
  - `nl_to_filters(text)` from `services.nl_search`
  - `COLUMNS` from `services.insight_query`
- Produces: HTTP responses at `/insights/`; URL name `"insights"`; context keys `form`, `entries`, `summary`, `site_title`

- [ ] **Step 1: Write failing view tests**

```python
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
                (("20261001","08:00","17:00",1,"João","ClienteA","Dev","CC-01","",""),),
                COLUMNS,
            )
            response = self.client.post("/insights/", {
                "dataInicio": "2026-10-01",
                "dataFim": "2026-10-31",
            })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Suspeitos: 0")
        self.assertContains(response, "Sem baseline: 1")

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
                (("20261001","08:00","17:00",1,"João","ClienteB","Dev","CC-01","",""),),
                COLUMNS,
            )
            response = self.client.post("/insights/", {
                "dataInicio": "2026-10-01",
                "dataFim": "2026-10-31",
            })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "🔴")
        self.assertContains(response, "entry-suspicious")
```

- [ ] **Step 2: Run tests and verify they fail**

```bash
python manage.py test InsightApp.tests.test_views
```
Expected: errors about missing `InsightApp.views` and `/insights/` returning 404

- [ ] **Step 3: Create `InsightApp/apps.py`**

```python
# InsightApp/apps.py
from django.apps import AppConfig


class InsightAppConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "InsightApp"
```

- [ ] **Step 4: Create `InsightApp/forms.py`**

```python
# InsightApp/forms.py
from django import forms
from AtividadeApp.forms import DateInput


class InsightFilterForm(forms.Form):
    nl_query = forms.CharField(
        required=False,
        label="Busca por linguagem natural",
        widget=forms.TextInput(attrs={
            "placeholder": "Busca por linguagem natural (em breve...)",
            "style": "width:100%; padding:0.6rem 0.8rem; border:1px solid #d1d8e0; "
                     "border-radius:6px; font-size:0.95rem; margin-bottom:0.75rem;",
        }),
    )
    dataInicio = forms.DateField(widget=DateInput, label="Data Início")
    dataFim = forms.DateField(widget=DateInput, label="Data Fim")
    nomeColaborador = forms.CharField(label="Colaborador", required=False)
    nomeCliente = forms.CharField(label="Cliente", required=False)
```

- [ ] **Step 5: Create `InsightApp/views.py`**

```python
# InsightApp/views.py
from django.shortcuts import render
from django.http import HttpRequest, HttpResponse
from django.contrib.auth.decorators import login_required
from datetime import date

from InsightApp.forms import InsightFilterForm
from services.insight_query import query_insight_entries
from services.outlier_detection import flag_outliers
from services.nl_search import nl_to_filters


def _build_query_params(cleaned_data: dict) -> dict:
    return {
        "dataInicio": date.strftime(cleaned_data["dataInicio"], "%Y%m%d"),
        "dataFim": date.strftime(cleaned_data["dataFim"], "%Y%m%d"),
        "nomeColaborador": cleaned_data.get("nomeColaborador") or None,
        "nomeCliente": cleaned_data.get("nomeCliente") or None,
    }


def _build_summary(entries: list[dict]) -> dict:
    return {
        "total": len(entries),
        "suspicious": sum(1 for e in entries if e["suspicious"]),
        "thin_baseline": sum(1 for e in entries if e["baseline_status"] == "insuficiente"),
    }


@login_required
def insights_view(request: HttpRequest) -> HttpResponse:
    form = InsightFilterForm()
    entries: list[dict] = []
    summary: dict = {}

    if request.method == "POST":
        form = InsightFilterForm(request.POST)
        if form.is_valid():
            params = _build_query_params(form.cleaned_data)

            # NL seam — implement nl_to_filters in services/nl_search.py to activate
            nl_text = form.cleaned_data.get("nl_query", "")
            nl_filters = nl_to_filters(nl_text) if nl_text else None
            if nl_filters:
                params.update(nl_filters)

            rows, columns = query_insight_entries(**params)
            entries = flag_outliers(rows, columns) if rows else []
            entries = sorted(entries, key=lambda e: (0 if e["suspicious"] else 1))
            summary = _build_summary(entries)

    return render(request, "InsightApp/insights.html", {
        "form": form,
        "entries": entries,
        "summary": summary,
        "site_title": "Insights de Lançamentos",
    })
```

- [ ] **Step 6: Create `InsightApp/urls.py`**

```python
# InsightApp/urls.py
from django.urls import path
from InsightApp import views

urlpatterns = [
    path("insights/", views.insights_view, name="insights"),
]
```

- [ ] **Step 7: Register app in `backOfficeProject/settings.py`**

Find `INSTALLED_APPS` (around line 38) and add `"InsightApp"` after `"AtividadeApp"`:

```python
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "AtividadeApp",
    "InsightApp",          # ← add this line
]
```

- [ ] **Step 8: Add URL include in `backOfficeProject/urls.py`**

```python
from django.contrib import admin
from django.urls import path, include
from AtividadeApp import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", views.main, name="main"),
    path("auth/login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("api/backOfficeData", views.api_get_data_view, name="getData"),
    path("", include("InsightApp.urls")),   # ← add this line
]
```

- [ ] **Step 9: Run tests — expect TemplateDoesNotExist**

```bash
python manage.py test InsightApp.tests.test_views
```
Expected: `django.template.exceptions.TemplateDoesNotExist: InsightApp/insights.html`

- [ ] **Step 10: Create template directory**

```bash
mkdir -p InsightApp/templates/InsightApp
```

- [ ] **Step 11: Create `InsightApp/templates/InsightApp/insights.html`**

Note: `base.html` has no Django template blocks, so this template includes `_head.html` directly — the same pattern `base.html` itself uses.

```html
{% include "AtividadeApp/partials/_head.html" %}
<body>
<div class="login-container">
  <div class="login-card" style="max-width: 98vw; width: 100%;">

    <style>
      .insight-filter-row { display: flex; gap: 1rem; flex-wrap: wrap; align-items: flex-end; margin-top: 0.5rem; }
      .insight-filter-group { display: flex; flex-direction: column; gap: 0.25rem; }
      .insight-filter-group label { font-size: 0.8rem; font-weight: 600; color: #34495e; text-transform: uppercase; letter-spacing: 0.5px; }
      .insight-filter-group input { padding: 0.6rem 0.8rem; border: 1px solid #d1d8e0; border-radius: 6px; font-size: 0.95rem; font-family: inherit; }
      .insight-submit { padding: 0.65rem 1.5rem; background: #1976D2; color: #fff; border: none; border-radius: 6px; font-size: 0.95rem; font-weight: 600; cursor: pointer; align-self: flex-end; text-transform: uppercase; letter-spacing: 0.4px; }
      .insight-submit:hover { background: #1565C0; }
      .summary-strip { margin: 1rem 0 0.5rem; display: flex; gap: 0.75rem; align-items: center; flex-wrap: wrap; }
      .badge { padding: 0.2rem 0.7rem; border-radius: 4px; font-size: 0.85rem; font-weight: 600; }
      .badge-gray { background: #6c757d; color: #fff; }
      .badge-red { background: #dc3545; color: #fff; }
      .badge-yellow { background: #ffc107; color: #333; }
      .insight-table { width: 100%; border-collapse: collapse; margin-top: 0.75rem; font-size: 0.88rem; }
      .insight-table th { background: #f5f7fa; padding: 0.45rem 0.7rem; text-align: left; border-bottom: 2px solid #d1d8e0; white-space: nowrap; font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.4px; color: #34495e; }
      .insight-table td { padding: 0.4rem 0.7rem; border-bottom: 1px solid #f0f0f0; vertical-align: top; }
      .entry-suspicious { background: #fff5f5; }
      .entry-suspicious td:first-child { border-left: 4px solid #dc3545; }
      .entry-thin { background: #fffbf0; }
      .entry-thin td:first-child { border-left: 4px solid #ffc107; }
      .insight-table tr:hover { background: #f8f9fa; }
      .entry-suspicious:hover { background: #ffe8e8; }
      .entry-thin:hover { background: #fff3cd; }
      .no-results { color: #6c757d; margin-top: 1rem; font-style: italic; }
    </style>

    <div class="page-title"><h2>Insights de Lançamentos</h2></div>

    <div class="user-message">
      <span>Olá, <strong>{{ user.username }}</strong>!
        <a href="{% url 'logout' %}"><strong>Trocar de conta</strong></a></span>
    </div>

    <form method="post">
      {% csrf_token %}
      <div class="form-field">
        {{ form.nl_query.label_tag }}
        {{ form.nl_query }}
      </div>
      <div class="insight-filter-row">
        <div class="insight-filter-group">
          {{ form.dataInicio.label_tag }}
          {{ form.dataInicio }}
        </div>
        <div class="insight-filter-group">
          {{ form.dataFim.label_tag }}
          {{ form.dataFim }}
        </div>
        <div class="insight-filter-group">
          {{ form.nomeColaborador.label_tag }}
          {{ form.nomeColaborador }}
        </div>
        <div class="insight-filter-group">
          {{ form.nomeCliente.label_tag }}
          {{ form.nomeCliente }}
        </div>
        <button type="submit" class="insight-submit">Buscar</button>
      </div>
      {% if form.errors %}
        <div class="message error" style="margin-top:0.5rem;">{{ form.errors }}</div>
      {% endif %}
    </form>

    {% if summary %}
    <div class="summary-strip">
      <span class="badge badge-gray">Total: {{ summary.total }}</span>
      <span class="badge badge-red">Suspeitos: {{ summary.suspicious }}</span>
      <span class="badge badge-yellow">Sem baseline: {{ summary.thin_baseline }}</span>
    </div>
    {% endif %}

    {% if entries %}
    <div style="overflow-x: auto;">
      <table class="insight-table">
        <thead>
          <tr>
            <th>Data</th>
            <th>Colaborador</th>
            <th>Cliente</th>
            <th>Atividade</th>
            <th>Centro Custo</th>
            <th>Início</th>
            <th>Fim</th>
            <th>Observação</th>
          </tr>
        </thead>
        <tbody>
          {% for entry in entries %}
          <tr class="{% if entry.suspicious %}entry-suspicious{% elif entry.baseline_status == 'insuficiente' %}entry-thin{% endif %}">
            <td>{{ entry.Data }}</td>
            <td title="{{ entry.reason|default:'' }}">
              {{ entry.Colaborador }}
              {% if entry.suspicious %} 🔴{% endif %}
              {% if entry.baseline_status == 'insuficiente' %} ⚠️{% endif %}
            </td>
            <td>{{ entry.NomeCliente }}</td>
            <td>{{ entry.DescricaoAtividade }}</td>
            <td>{{ entry.CentroCusto }}</td>
            <td>{{ entry.HoraInicio }}</td>
            <td>{{ entry.HoraFim }}</td>
            <td>{{ entry.Observacao1 }}{% if entry.Observacao2 %} / {{ entry.Observacao2 }}{% endif %}</td>
          </tr>
          {% endfor %}
        </tbody>
      </table>
    </div>
    {% elif summary %}
      <p class="no-results">Nenhum registro encontrado para o período selecionado.</p>
    {% endif %}

  </div>
</div>
</body>
</html>
```

- [ ] **Step 12: Run all InsightApp tests**

```bash
python manage.py test InsightApp
```
Expected: `OK` — all tests pass (approximately 19 tests across 4 files)

- [ ] **Step 13: Smoke-test manually**

```bash
python manage.py runserver
```
Open `http://127.0.0.1:8000/insights/`. Verify:
- Redirects to login if not authenticated
- After login: form renders with NL box, date pickers, Buscar button
- Submitting a date range returns a table (or "Nenhum registro" if period has no data)
- No 500 errors in the terminal

- [ ] **Step 14: Commit**

```bash
git add InsightApp/ backOfficeProject/settings.py backOfficeProject/urls.py
git commit -m "feat: add InsightApp with HTML table and statistical outlier detection"
```
