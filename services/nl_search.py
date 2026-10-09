# services/nl_search.py


def nl_to_filters(text: str) -> dict | None:
    """
    Translate a natural-language query into filter parameters.

    TODO: implement with an LLM (e.g. Claude API).
    Return a dict with any subset of keys:
        dataInicio, dataFim, nomeColaborador, nomeCliente, atividade, centroCusto
    Return None if text cannot be parsed — the view ignores NL input gracefully.

    Example return value:
        {"nomeColaborador": "João", "nomeCliente": "Sinosbyte", "dataInicio": "20260101"}
    """
    return None  # stub
