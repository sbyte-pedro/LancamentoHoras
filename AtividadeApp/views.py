# from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.contrib import messages, auth
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from datetime import datetime, date
from AtividadeApp.forms import FiltrosForm
from services.defToExcel import gerarExcel
from services.defToJson import gerarDict


dataInicio = 0
dataFim = 0
minCodColaborador = 0
maxCodColaborador = 0
Cliente = 0
maxCliente = 0
Atividade = 0
maxAtividade = 0
CentroCusto = 0
maxCentroCusto = 0


@login_required
def main(request: HttpRequest) -> HttpResponse:
    filtros_form = FiltrosForm()
    if request.method == "POST":
        filtros_form = FiltrosForm(request.POST)
        if filtros_form.is_valid():
            dados = filtros_form.cleaned_data
            dataInicio: date = dados.get("dataInicio")  # type: ignore
            dataFim: date = dados.get("dataFim")  # type: ignore
            minCodColaborador: int | None = dados.get("minCodColaborador")
            maxCodColaborador = dados.get("maxCodColaborador")
            minCliente = dados.get("minCliente")
            maxCliente = dados.get("maxCliente")
            minAtividade = dados.get("minAtividade")
            maxAtividade = dados.get("maxAtividade")
            minCentroCusto = dados.get("minCentroCusto")
            maxCentroCusto = dados.get("maxCentroCusto")

            wb = gerarExcel(
                date.strftime(dataInicio, "%Y%m%d"),
                date.strftime(dataFim, "%Y%m%d"),
                minCodColaborador,
                maxCodColaborador,
                minCliente,
                maxCliente,
                minAtividade,
                maxAtividade,
                minCentroCusto,
                maxCentroCusto,
            )
            response = HttpResponse(content_type="application/ms-excel")

            today = datetime.now()
            responseContent = f"attachment; filename = AtividadeIntegracoes{today.hour}{today.minute}{today.second} {today.day}-{today.month}-{today.year}.xlsx"

            response["Content-Disposition"] = responseContent

            wb.save(response)  # type: ignore

            return response

    context = {"form": filtros_form, "site_title": "Lancamento de Horas"}
    return render(request, "AtividadeApp/base.html", context=context)


def login_view(request):
    form = AuthenticationForm(request)
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            auth.login(request, user)
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
    dataInicio = (
        request.GET.get("dataInicio")
        if request.GET.get("dataInicio") is not None
        else datetime.now().date().strftime("%Y%m%d")
    )
    dataFim = (
        request.GET.get("dataFim")
        if request.GET.get("dataFim") is not None
        else datetime.now().date().strftime("%Y%m%d")
    )
    minCodColaborador = (
        request.GET.get("minCodColaborador")
        if request.GET.get("minCodColaborador") is not None
        else 0
    )
    maxCodColaborador = (
        request.GET.get("maxCodColaborador")
        if request.GET.get("maxCodColaborador") is not None
        else 99
    )
    minCodCliente = (
        request.GET.get("minCodCliente")
        if request.GET.get("minCodCliente") is not None
        else 0
    )
    maxCodCliente = (
        request.GET.get("maxCodCliente")
        if request.GET.get("maxCodCliente") is not None
        else 0
    )
    minAtividade = (
        request.GET.get("minAtividade")
        if request.GET.get("minAtividade") is not None
        else 0
    )
    maxAtividade = (
        request.GET.get("maxAtividade")
        if request.GET.get("maxAtividade") is not None
        else 0
    )
    minCentroCusto = (
        request.GET.get("minCentroCusto")
        if request.GET.get("minCentroCusto") is not None
        else 0
    )
    maxCentroCusto = (
        request.GET.get("maxCentroCusto")
        if request.GET.get("maxCentroCusto") is not None
        else "Z" * 10
    )

    data = gerarDict(
        dataInicio,
        dataFim,
        minCodColaborador,
        maxCodColaborador,
        minCodCliente,
        maxCodCliente,
        minAtividade,
        maxAtividade,
        minCentroCusto,
        maxCentroCusto,
    )

    return JsonResponse(
        data,
    )
