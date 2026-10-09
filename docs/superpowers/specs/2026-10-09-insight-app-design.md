# InsightApp — Design Spec
**Date:** 2026-10-09  
**Status:** Approved

---

## Goal

A second screen in the LancamentoHoras Django project where a manager can view work-hour entries (lançamentos) rendered as HTML and immediately spot statistically suspicious entries from employees — entries that fall outside that employee's normal distribution of clients, activities, and cost centers.

Natural-language search is planned but will be implemented by the developer; this spec defines the seam.

---

## What We Are Not Building (Yet)

- NL→SQL translation (stub only — seam is defined, implementation left to developer)
- Email data ingestion
- AI/LLM per-entry judgment (Phase 2)
- Any new Django model or local data persistence (full history already lives in `back_office` MySQL)

---

## Architecture

New `InsightApp/` Django app added to the existing project alongside `AtividadeApp/`. It shares auth, base templates, and DB credentials but has no code dependency on `AtividadeApp`.

```
InsightApp/
├── __init__.py
├── apps.py
├── views.py                  ← single view: insights_view
├── forms.py                  ← InsightFilterForm (date range + NL text box)
├── urls.py                   ← path("insights/", ...)
└── templates/
    └── InsightApp/
        └── insights.html     ← extends AtividadeApp/base.html

services/
├── selectData.py             ← unchanged (existing)
├── insight_query.py          ← NEW: raw entries for a given period
├── outlier_detection.py      ← NEW: per-employee baseline + flag logic
└── nl_search.py              ← NEW: stub — nl_to_filters(text) → dict | None
```

`backOfficeProject/urls.py` gains one `include("InsightApp.urls")`. The screen is at `/insights/`.

Auth: `@login_required` — same as the existing `main` view.

---

## Data Flow

```
insights_view (POST)
    │
    ├─► insight_query.py        ← Query 1: entries for selected period (date range)
    │       returns: list[dict] with columns:
    │           Data, HoraInicio, HoraFim, Colaborador, CodColaborador,
    │           NomeCliente, DescricaoAtividade, CentroCusto,
    │           Observacao1, Observacao2
    │
    ├─► outlier_detection.py    ← Query 2: 12-month baseline for each employee in results
    │       returns: same list[dict], each entry gains:
    │           suspicious: bool
    │           reason: str | None
    │           baseline_status: "ok" | "insuficiente"
    │
    └─► insights.html           ← renders enriched list; flagged rows float to top
```

---

## Service: `services/insight_query.py`

Fires the same joins as `selectData.py` (`ra_atividade_trabalho` → `atividade`, `colaboradores`, `pessoa`, `new_centro_custo`, `emitente`) but accepts only:

- `dataInicio: str` (YYYYMMDD)
- `dataFim: str` (YYYYMMDD)
- `nomeColaborador: str | None` (optional, filters by `pessoa.nome LIKE %s`)
- `nomeCliente: str | None` (optional, filters by `em.nome_abrev LIKE %s`)
- `atividade: str | None` (optional)
- `centroCusto: str | None` (optional)

Returns `(rows: tuple, columns: tuple)` — same contract as `selectDataFromDatabase`.

---

## Service: `services/outlier_detection.py`

### Baseline Query

Takes the unique `CodColaborador` values from the current results and fires **one** aggregation query covering the **last 12 months**:

```sql
SELECT
    colab.cod_colaborador,
    em.nome_abrev        AS cliente,
    ativ.desc_atividade  AS atividade,
    COUNT(*)             AS qtd
FROM ra_atividade_trabalho rat
INNER JOIN colaboradores colab ON rat.cod_colaborador = colab.cod_colaborador
INNER JOIN atividade ativ      ON rat.atividade_cod_atividade = ativ.cod_atividade
INNER JOIN emitente em         ON rat.cod_emitente = em.cod_emitente
WHERE rat.cod_colaborador IN (...)
  AND rat.data_atividade_s >= %s   -- 12 months ago
  AND rat.data_atividade_s <= %s   -- today
GROUP BY colab.cod_colaborador, em.nome_abrev, ativ.desc_atividade
```

In memory this becomes:

```python
{
    42: {  # cod_colaborador
        "total": 180,
        "clients":    {"ClienteA": 0.92, "ClienteB": 0.06, "ClienteC": 0.02},
        "activities": {"Desenvolvimento": 0.80, "Suporte": 0.20},
    },
    ...
}
```

### Flagging Rules

- **Thin baseline:** employee has `total < 20` entries → `baseline_status = "insuficiente"`, `suspicious = False`. Not flagged.
- **Client outlier:** entry's `NomeCliente` appears in `< 5%` of employee's baseline clients → `suspicious = True`
- **Activity outlier:** entry's `DescricaoAtividade` appears in `< 5%` of employee's baseline activities → `suspicious = True`
- Either condition alone is sufficient to flag. Both can be flagged simultaneously.

### Reason String (Portuguese)

```
"Cliente 'Sinosbyte' representa apenas 2% do histórico de João Silva (últimos 12 meses)"
"Atividade 'Auditoria' representa apenas 1% do histórico de João Silva (últimos 12 meses)"
```

If both client and activity are outliers, reason strings are joined with `" | "`.

### Thresholds (configurable constants at top of file)

```python
OUTLIER_THRESHOLD = 0.05      # 5%
MIN_BASELINE_ENTRIES = 20
BASELINE_MONTHS = 12
```

---

## Service: `services/nl_search.py` (Stub)

```python
def nl_to_filters(text: str) -> dict | None:
    """
    Translate a natural-language query into filter parameters.

    TODO: implement with an LLM (e.g. Claude API).
    Return a dict with any subset of:
        dataInicio, dataFim, nomeColaborador, nomeCliente, atividade, centroCusto
    Return None if text cannot be parsed — view will ignore NL input gracefully.

    Example return:
        {"nomeColaborador": "João", "nomeCliente": "Sinosbyte", "dataInicio": "20260101"}
    """
    return None  # stub
```

---

## View: `InsightApp/views.py`

```python
@login_required
def insights_view(request):
    form = InsightFilterForm()
    entries = []
    summary = {}
    if request.method == "POST":
        form = InsightFilterForm(request.POST)
        if form.is_valid():
            params = _build_query_params(form.cleaned_data)
            # NL seam — four lines, never touch after implementing nl_to_filters
            nl_text = form.cleaned_data.get("nl_query", "")
            nl_filters = nl_to_filters(nl_text) if nl_text else None
            if nl_filters:
                params.update(nl_filters)
            rows, columns = query_entries(params)
            entries = flag_outliers(rows, columns)
            summary = _build_summary(entries)
    return render(request, "InsightApp/insights.html",
                  {"form": form, "entries": entries, "summary": summary})
```

---

## Form: `InsightApp/forms.py`

Fields:
- `nl_query` — `CharField(required=False)` — full width, top of form, placeholder *"Busca por linguagem natural (em breve...)"*
- `dataInicio` — `DateField(widget=DateInput)`
- `dataFim` — `DateField(widget=DateInput)`
- `nomeColaborador` — `CharField(required=False)`
- `nomeCliente` — `CharField(required=False)`

---

## Template: `InsightApp/templates/InsightApp/insights.html`

Extends `AtividadeApp/base.html`. Three visual zones:

**Zone 1 — Filter bar**
Compact horizontal form. NL box full-width on top row. Date pickers + optional filters on second row. "Buscar" button.

**Zone 2 — Summary strip** (only shown after a search)
- Total de registros: N
- Suspeitos: N (red badge)
- Sem baseline suficiente: N (yellow badge)

**Zone 3 — Entries table**
Columns: `Data | Colaborador | Cliente | Atividade | Centro Custo | Início | Fim | Observação`

- Suspicious rows: red left border (`border-left: 4px solid #dc3545`) + light red background (`#fff5f5`), float to top
- Reason shown via `title` attribute on the `Colaborador` cell (tooltip on hover, no JS required)
- A small 🔴 icon appended to the collaborator name in flagged rows
- Thin-baseline employees: yellow left border + `title="Baseline insuficiente (menos de 20 registros nos últimos 12 meses)"`

Inline `<style>` block in the template — no new CSS file, no new dependencies.

---

## URL Configuration

`InsightApp/urls.py`:
```python
from django.urls import path
from InsightApp import views

urlpatterns = [
    path("insights/", views.insights_view, name="insights"),
]
```

`backOfficeProject/urls.py` adds:
```python
path("", include("InsightApp.urls")),
```

---

## Tests: `InsightApp/tests.py`

### `OutlierDetectionTests` (unit, no DB)
- Employee >5% history for client → not flagged
- Employee <5% history for client → flagged with correct reason string (Portuguese)
- Employee <20 baseline entries → `baseline_status = "insuficiente"`, `suspicious = False`
- Both client and activity outliers → reason strings joined with `" | "`

### `InsightQueryTests`
- Returns correct column tuple
- Empty result for date range with no data (mock PyMySQL)

### `InsightViewTests` (Django test client)
- Unauthenticated GET → redirect to login
- Authenticated GET `/insights/` → 200, form renders
- Authenticated POST with valid date range → 200, table renders
- `nl_to_filters` returning `None` → NL input silently ignored (no error)

---

## Out of Scope (future phases)

| Phase | What |
|-------|------|
| 2 | LLM per-entry anomaly judgment with narrative reason |
| 3 | NL search implementation (seam is ready) |
| 4 | Email data ingestion |
| 5 | Caching employee baselines (only if query performance becomes a problem) |
