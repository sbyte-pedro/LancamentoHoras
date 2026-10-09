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
