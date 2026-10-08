from django.shortcuts import render, redirect
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.contrib import messages, auth
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from datetime import datetime, date

from AtividadeApp.forms import FiltrosForm
from AtividadeApp.services import exportar_excel, exportar_json


def _build_excel_response(wb) -> HttpResponse:
    now = datetime.now()
    filename = (
        f"AtividadeIntegracoes{now.hour}{now.minute}{now.second}"
        f" {now.day}-{now.month}-{now.year}.xlsx"
    )
    response = HttpResponse(content_type="application/ms-excel")
    response["Content-Disposition"] = f"attachment; filename={filename}"
    wb.save(response)
    return response


def _form_filter_params(cleaned_data: dict) -> dict:
    return {
        "dataInicio": date.strftime(cleaned_data["dataInicio"], "%Y%m%d"),
        "dataFim": date.strftime(cleaned_data["dataFim"], "%Y%m%d"),
        "minCodColaborador": cleaned_data.get("minCodColaborador"),
        "maxCodColaborador": cleaned_data.get("maxCodColaborador"),
        "nomeCliente": cleaned_data.get("minCliente"),
        "fimNomeCliente": cleaned_data.get("maxCliente"),
        "atividade": cleaned_data.get("minAtividade"),
        "fimAtividade": cleaned_data.get("maxAtividade"),
        "centroCusto": cleaned_data.get("minCentroCusto"),
        "fimCentroCusto": cleaned_data.get("maxCentroCusto"),
    }


def _api_filter_params(query_dict) -> dict:
    today = datetime.now().date().strftime("%Y%m%d")
    return {
        "dataInicio": query_dict.get("dataInicio", today),
        "dataFim": query_dict.get("dataFim", today),
        "minCodColaborador": query_dict.get("minCodColaborador", 0),
        "maxCodColaborador": query_dict.get("maxCodColaborador", 99),
        "nomeCliente": query_dict.get("minCodCliente", 0),
        "fimNomeCliente": query_dict.get("maxCodCliente", 0),
        "atividade": query_dict.get("minAtividade", 0),
        "fimAtividade": query_dict.get("maxAtividade", 0),
        "centroCusto": query_dict.get("minCentroCusto", 0),
        "fimCentroCusto": query_dict.get("maxCentroCusto", "Z" * 10),
    }


@login_required
def main(request: HttpRequest) -> HttpResponse:
    filtros_form = FiltrosForm()
    if request.method == "POST":
        filtros_form = FiltrosForm(request.POST)
        if filtros_form.is_valid():
            wb = exportar_excel(_form_filter_params(filtros_form.cleaned_data))
            return _build_excel_response(wb)

    context = {"form": filtros_form, "site_title": "Lancamento de Horas"}
    return render(request, "AtividadeApp/base.html", context=context)


def login_view(request):
    form = AuthenticationForm(request)
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            auth.login(request, form.get_user())
            return redirect("main")
        messages.error(request, "Houve um erro no user ou na senha")
    context = {"form": form, "site_title": "Login "}
    return render(request, "AtividadeApp/login.html", context)


def logout_view(request):
    auth.logout(request)
    messages.warning(request, "Usuário deslogado com sucesso")
    return redirect("login")


@login_required
def api_get_data_view(request):
    data = exportar_json(_api_filter_params(request.GET))
    return JsonResponse(data)
