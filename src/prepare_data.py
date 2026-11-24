import logging
from pathlib import Path

import duckdb

log = logging.getLogger(__name__)

RAIZ = Path(__file__).resolve().parent.parent
RAW = RAIZ / 'data' / 'raw'
PROCESSED = RAIZ / 'data' / 'processed'
LIMITE_ATRASO_MIN = 15

def contar(con, tabela: str, rotulo: str) -> int:
    n = con.sql(f'SELECT count(*) FROM {tabela}').fetchall()[0][0]
    log.info('%-40s %s linhas', rotulo, f'{n:,}')
    return n

def ler_bruto(con) -> None:
    con.sql(f"""
        CREATE OR REPLACE TABLE bruto AS
        SELECT
            "ICAO Empresa Aérea" AS empresa,
            "Número Voo" AS numero_voo,
            "Código Autorização (DI)" AS codigo_di,
            "Código Tipo Linha" AS tipo_linha,
            "ICAO Aeródromo Origem"     AS origem,
            "ICAO Aeródromo Destino"    AS destino,
            TRY_CAST("Partida Prevista" AS TIMESTAMP) AS partida_prevista,
            TRY_CAST("Partida Real"     AS TIMESTAMP) AS partida_real,
            "Situação Voo"              AS situacao
        FROM read_csv('{RAW.as_posix()}/VRA_*.csv',
                      delim=';', skip=1, header=true, nullstr='null',
                      all_varchar=true, union_by_name=true)
    """)

def filtrar_e_limpar(con) -> None:
    con.sql("""
        CREATE OR REPLACE TABLE domestico AS
        SELECT *
        FROM bruto
        WHERE "tipo_linha" = 'N'
    """)
    contar(con, 'domestico', "Tipo de linha 'N' (doméstica)")

    con.sql("""
        CREATE OR REPLACE TABLE sem_di_duplicada AS
        SELECT * FROM domestico WHERE
            codigo_di = '0' 
            OR codigo_di = '2' 
            OR codigo_di = '4'
    """)
    contar(con, 'sem_di_duplicada', 'Sem_etapa_duplicada')

    con.sql("""
        CREATE OR REPLACE TABLE com_previsao AS
        SELECT * FROM sem_di_duplicada
        WHERE partida_prevista IS NOT NULL
    """)
    contar(con, 'com_previsao', 'Com partida prevista')

    con.sql("""
        CREATE OR REPLACE TABLE limpo AS
        SELECT * FROM com_previsao
        QUALIFY row_number() OVER (
            PARTITION BY 
                empresa,
                numero_voo,
                origem,
                partida_prevista
            ORDER BY 
                (situacao = 'REALIZADO') DESC,
                (partida_real IS NOT NULL) DESC,
                codigo_di
        ) = 1
    """)
    contar(con, 'limpo', 'Sem duplicados')

def criar_variaveis(con) -> None:
    con.sql("""
        CREATE OR REPLACE TABLE com_variaveis AS
        SELECT
            *,
            origem || '-' || destino as rota,
            hour(partida_prevista) AS hora_prevista,
            isodow(partida_prevista) AS dia_semana,
            month(partida_prevista) AS mes,
            year(partida_prevista) AS ano,
            count(*) OVER (PARTITION BY origem, date_trunc('hour', partida_prevista)) AS voos_na_hora
        FROM limpo
        """)
    contar(con, 'com_variaveis', 'Com variáveis')

def separar_e_criar_alvo(con) -> None:
    con.sql("""
        CREATE OR REPLACE TABLE cancelados AS
        SELECT * FROM com_variaveis
        WHERE situacao = 'CANCELADO'
    """)
    contar(con, 'cancelados', 'Cancelados')

    con.sql("""
        CREATE OR REPLACE TABLE voos AS
        SELECT * FROM com_variaveis
        WHERE situacao = 'REALIZADO'
            AND partida_real IS NOT NULL
            AND ano BETWEEN 2023 AND 2025
    """)
    contar(con, 'voos', 'Voos realizados')

    con.sql(f"""
        CREATE OR REPLACE TABLE atraso_min AS
        SELECT
            *,
            date_diff('second', partida_prevista, partida_real) / 60 AS atraso_min,
            CAST(date_diff('second', partida_prevista, partida_real) / 60
                > {LIMITE_ATRASO_MIN} AS INTEGER) AS atrasado,
            CASE ano 
                WHEN 2023 THEN 'treino'
                WHEN 2024 THEN 'validacao'
                WHEN 2025 THEN 'teste' END AS conjunto
        FROM voos
    """)
    contar(con, 'atraso_min', 'Voos realizados (com alvo)')

def salvar(con) -> None:
    PROCESSED.mkdir(parents=True, exist_ok=True)
    con.sql(f"COPY atraso_min TO '{(PROCESSED / 'voos.parquet').as_posix()}' (FORMAT PARQUET)")
    con.sql(f"COPY cancelados TO '{(PROCESSED / 'cancelados.parquet').as_posix()}' (FORMAT PARQUET)")
    con.sql("SELECT count(*) FROM 'data/processed/voos.parquet'").show()

def main() -> None:
    con = duckdb.connect()
    ler_bruto(con)
    contar(con, 'bruto', 'Registros brutos')
    filtrar_e_limpar(con)
    criar_variaveis(con)
    separar_e_criar_alvo(con)
    salvar(con)
    
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
    main()