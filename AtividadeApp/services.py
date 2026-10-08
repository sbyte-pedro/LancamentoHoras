from openpyxl import Workbook

from services.defToExcel import gerarExcel as _gerarExcel
from services.defToJson import gerarDict as _gerarDict


def exportar_excel(params: dict) -> Workbook:
    return _gerarExcel(**params)


def exportar_json(params: dict) -> dict:
    return _gerarDict(**params)
