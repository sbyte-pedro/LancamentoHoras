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
