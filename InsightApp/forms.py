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
