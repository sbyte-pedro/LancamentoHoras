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
