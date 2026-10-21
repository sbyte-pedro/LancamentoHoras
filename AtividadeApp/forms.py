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
        label="Codigo Colaborador", initial=0, required=False
    )
    maxCodColaborador = forms.IntegerField(label="Código Colaborador", initial=99)

    minCliente = forms.CharField(label="Código Cliente", required=False)
    maxCliente = forms.CharField(label="Código Cliente", initial="ZZZZZZZZZZZZZZZ")

    minAtividade = forms.CharField(label="Atividade", required=False)
    maxAtividade = forms.CharField(label="Atividade", initial="ZZZZZZZZZZZZZZZ")

    minCentroCusto = forms.CharField(label="Centro Custo", required=False)
    maxCentroCusto = forms.CharField(label="Centro Custo", initial="ZZZZZZZZZZZZZZZ")
