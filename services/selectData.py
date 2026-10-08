import os
from datetime import datetime
import pymysql
from dotenv import load_dotenv

load_dotenv()


def selectDataFromDatabase(
    dataInicio: str = "20230101",
    dataFim: str = "20230101",
    minCodColaborador: int | None = 0,
    maxCodColaborador: int | None = 99,
    nomeCliente: int | None = 0,
    fimNomeCliente: int | None = 0,
    atividade: int | None = 0,
    fimAtividade: int | None = 0,
    centroCusto: int | None = 0,
    fimCentroCusto: str | None = "Z" * 10,
) -> tuple[tuple, tuple]:
    inicio = datetime.now()
    print(
        f"PARAMETROS: {dataInicio,dataFim,minCodColaborador,maxCodColaborador,nomeCliente, fimNomeCliente,atividade, fimAtividade, centroCusto, fimCentroCusto}"
    )
    connection = pymysql.connect(
        host=os.environ["DB_HOST"],
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        database=os.environ.get("DB_NAME", "back_office"),
    )
    with connection:
        with connection.cursor() as cursor:
            queryUpdate = """
            UPDATE
                ra_atividade_trabalho ra
                SET
                    ra.atividade_cod_atividade =   (SELECT
                cod_atividade
                    FROM
                        atividade
                    WHERE
                        desc_atividade = ra.desc_atividade limit 1)
                WHERE
                    atividade_cod_atividade is null"""
            cursor.execute(queryUpdate)
            connection.commit()

            querySelect = """
            SELECT
                this_.data_atividade_s as DataAtividade,
                this_.hora_inicio_s as HoraInicio,
                this_.hora_final_s as HoraFim,
                this_.atividade_cod_atividade as CodAtividade,
                this_.observacao1 as Observacao1,
                this_.observacao2 as Observacao2,
                pessoa.nome as nomeColaborador,
                ativ.desc_atividade as descricaoAtividade,
                em.nome_abrev as nomeCliente,
                ncc.descricao as CentroCusto
            FROM
                ra_atividade_trabalho this_
            INNER JOIN
                atividade ativ
                    on this_.atividade_cod_atividade=ativ.cod_atividade
            INNER JOIN
                colaboradores colab
                    ON this_.cod_colaborador=colab.cod_colaborador
            INNER JOIN
                pessoa
                    ON colab.cod_pessoa=pessoa.cod_pessoa
            INNER JOIN
                new_centro_custo ncc
                    ON ativ.centroCusto_id=ncc.id
            INNER JOIN
                emitente em
                    on this_.cod_emitente=em.cod_emitente
            WHERE
                this_.data_atividade_s>= %s
                AND this_.data_atividade_s<= %s
                AND this_.cod_colaborador>= %s
                AND this_.cod_colaborador<= %s
                AND em.nome_abrev>= %s
                AND em.nome_abrev<= %s
                AND ativ.desc_atividade>= %s
                AND ativ.desc_atividade<= %s
                AND ncc.codigo>= %s
                AND ncc.codigo<= %s;
                
            """
            dados = (
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
            cursor.execute(querySelect, dados)

            ativTrabalho: tuple = cursor.fetchall()
            columns: tuple = (
                "Data",
                "HoraInicio",
                "HoraFim",
                "CodAtividade",
                "Observacao1",
                "Observacao2",
                "Colaborador",
                "DescricaoAtividade",
                "NomeCliente",
                "CentroCusto",
            )

    print(
        f"Tempo demorado para pegar {len(ativTrabalho)} registros do banco de dados: {datetime.now() - inicio}"
    )

    return ativTrabalho, columns
