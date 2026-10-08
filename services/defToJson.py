from services.selectData import selectDataFromDatabase
from services.defToExcel import transformaParaDf
from datetime import date
from services.utils import passarParaDecimal
import pandas as pd


def gerarDict(
    dataInicio: str = "20230101",
    dataFim: str = "20230101",
    minCodColaborador=0,
    maxCodColaborador=99,
    nomeCliente: int = 0,
    fimNomeCliente: int = 0,
    atividade: int = 0,
    fimAtividade: int = 0,
    centroCusto: int = 0,
    fimCentroCusto: str = "Z" * 10,
) -> dict:

    ativTrabalho, columns = selectDataFromDatabase(
        dataInicio,
        dataFim,
        minCodColaborador,
        maxCodColaborador,
        nomeCliente,
        fimNomeCliente,
        atividade,
        fimAtividade,
        centroCusto,
        fimCentroCusto,
    )

    ativTrabalhoDf = transformaParaDf(ativTrabalho, columns)
    if len(ativTrabalhoDf) == 0:
        return {"Erro:": "Com esses filtros não retornou nenhum dado"}

    dictFinal = {"Resumo Atividade": [], "atividades": []}
    c = 1
    for desc_atividade in ativTrabalhoDf["DescricaoAtividade"].unique().tolist():
        if pd.isnull(desc_atividade):
            continue
        c += 1
        atividadeTrabalho = ativTrabalhoDf[
            ativTrabalhoDf["DescricaoAtividade"] == desc_atividade
        ]

        atividadeTrabalho["Data"] = [
            date(x.year, x.month, x.day) for x in atividadeTrabalho["Data"]
        ]

        atividadeTrabalho = atividadeTrabalho.sort_values(by="Data")

        atividadeTrabalho["Data"] = [
            date.strftime(data, "%d/%m/%Y") for data in atividadeTrabalho["Data"]
        ]

        qtdHoras = 0
        qtdMinutos = 0
        for x in atividadeTrabalho["Qtde Horas"]:
            if len(x) == 4:
                qtdHoras += int(x[0])
                qtdMinutos += int(x[2:])
            elif len(x) == 5:
                qtdHoras += int(x[:2])
                qtdMinutos += int(x[3:])

        horasDosMinutos = qtdMinutos // 60
        qtdHoras += horasDosMinutos
        qtdMinutos -= horasDosMinutos * 60
        if len(str(qtdMinutos)) == 1:
            qtdMinutos = "00"

        title = desc_atividade.replace(":", "-")
        title = title.replace("/", "|")

        atividadeTrabalho["Qtde Horas Decimal"] = atividadeTrabalho["Qtde Horas"]

        atividadeTrabalho["Qtde Horas Decimal"] = atividadeTrabalho[
            "Qtde Horas Decimal"
        ].apply(lambda x: passarParaDecimal(x))

        dictAtividade = {
            "atividade": title,
            "cliente": str(atividadeTrabalho.iloc[0, 4]),
            "centroCusto": str(atividadeTrabalho.iloc[0, 5]),
            "qtde_horas_totais": f"{qtdHoras}:{qtdMinutos}",
            "registros": [],
        }

        atividadeTrabalho = atividadeTrabalho[
            ["Data", "Qtde Horas", "Qtde Horas Decimal", "Descricao", "Colaborador"]
        ]

        for _, row in atividadeTrabalho.iterrows():
            dictAtividade["registros"].append(
                {
                    "data": row["Data"],
                    "qtde_horas": row["Qtde Horas"],
                    "qtde_horas_decimal": row["Qtde Horas Decimal"],
                    "descricao": row["Descricao"],
                    "colaborador": row["Colaborador"],
                }
            )
        dictFinal["atividades"].append(dictAtividade)
        horaMinuto = f"{qtdHoras}:{qtdMinutos}"
        horaMinutoDecimal = passarParaDecimal(horaMinuto)

        atividadeResumo = {
            "desc_atividade": desc_atividade,
            "hora_minutos": horaMinuto,
            "hora_decimal": horaMinutoDecimal,
        }

        dictFinal["Resumo Atividade"].append(atividadeResumo)

    return dictFinal
