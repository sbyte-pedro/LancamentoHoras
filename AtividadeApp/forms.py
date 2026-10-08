from django import forms


class DateInput(forms.DateInput):
    input_type = "date"


class FiltrosForm(forms.Form):
    dataInicio = forms.DateField(
        widget=DateInput, label="Data Início",
    )
    dataFim = forms.DateField(
        widget=DateInput, label="Data Fim",
    )

    minCodColaborador = forms.IntegerField(
        label="Colaborador (De)", initial=0, required=False
    )
    maxCodColaborador = forms.IntegerField(label="Colaborador (Até)", initial=99)

    minCliente = forms.CharField(label="Cliente (De)", required=False)
    maxCliente = forms.CharField(label="Cliente (Até)", initial="ZZZZZZZZZZZZZZZ")

    minAtividade = forms.CharField(label="Atividade (De)", required=False)
    maxAtividade = forms.CharField(label="Atividade (Até)", initial="ZZZZZZZZZZZZZZZ")

    minCentroCusto = forms.CharField(label="Centro Custo (De)", required=False)
    maxCentroCusto = forms.CharField(label="Centro Custo (Até)", initial="ZZZZZZZZZZZZZZZ")
