import logging
from pathlib import Path

import duckdb

log = logging.getLogger(__name__)

RAIZ = Path(__file__).resolve().parent.parent
RAW = RAIZ / 'data' / 'raw'
PROCESSED = RAIZ / 'data' / 'processed'
LIMITE_ATRASO_MIN = 15
N_AEROPORTOS = 16
MIN_VOOS_ROTA = 500

# Conta a quantidade de linhas nas tabelas geradas pelas funções de preparação de dados e registra no log.
def contar(con, tabela: str, rotulo: str) -> int:
    n = con.sql(f'SELECT count(*) FROM {tabela}').fetchall()[0][0]
    log.info('%-40s %s linhas', rotulo, f'{n:,}')
    return n

# Traz o csv bruto para uma tabela DuckDB, renomeando colunas e convertendo datas.
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

# Filtra e limpa os dados, removendo voos internacionais, etapas duplicadas e voos sem previsão de partida.
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

# Cria variáveis derivadas, como rota, hora prevista, dia da semana, mês, ano e quantidade de voos na mesma hora.
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

# Separa os voos cancelados e realizados, cria a variável alvo (atrasado) e define o 
# conjunto (treino, validação ou teste) com base no ano.
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
        CREATE OR REPLACE TABLE voos_alvo AS
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
    contar(con, 'voos_alvo', 'Voos realizados (com alvo)')

# Seleciona os 16 aeroportos com mais voos no conjunto de treino e as rotas entre eles com pelo menos 500 voos, 
# criando tabelas separadas para aeroportos, rotas e voos selecionados.
def selecionar_aeroportos(con) -> None:
    con.sql(f"""
    CREATE OR REPLACE TABLE aeroportos_sel AS
    SELECT origem
        FROM voos_alvo
        WHERE conjunto = 'treino'
        GROUP BY origem
        ORDER BY count(*) DESC, origem
        LIMIT {N_AEROPORTOS}
    """)
    contar(con, 'aeroportos_sel', 'Aeroportos selecionados')

    con.sql(f"""
        CREATE OR REPLACE TABLE rotas_sel AS
        SELECT origem, destino, count(*) AS n
        FROM voos_alvo
        WHERE conjunto = 'treino'
          AND origem  IN (SELECT origem FROM aeroportos_sel)
          AND destino IN (SELECT origem FROM aeroportos_sel)
        GROUP BY origem, destino
        HAVING count(*) >= {MIN_VOOS_ROTA}
        """)
    contar(con, 'rotas_sel', 'Rotas selecionadas')
    
    con.sql("""
        CREATE OR REPLACE TABLE voos_sel AS
        SELECT v.*
        FROM voos_alvo v
        JOIN rotas_sel r
        ON v.origem = r.origem AND v.destino = r.destino
        """)
    contar(con, 'voos_sel', 'Voos nas rotas selecionadas')

    por_conjunto = con.sql("""
        SELECT conjunto, count(*) AS n
        FROM voos_sel GROUP BY conjunto ORDER BY conjunto
    """).fetchall()
    for conjunto, n in por_conjunto:
        log.info('  %-12s %s voos', conjunto, f'{n:,}')

# Salva as tabelas finais em arquivos Parquet na pasta de dados processados.
def salvar(con) -> None:
    PROCESSED.mkdir(parents=True, exist_ok=True)
    con.sql(f"COPY voos_alvo TO '{(PROCESSED / 'voos.parquet').as_posix()}' (FORMAT PARQUET)")
    con.sql(f"COPY cancelados TO '{(PROCESSED / 'cancelados.parquet').as_posix()}' (FORMAT PARQUET)")
    con.sql(f"COPY voos_sel TO '{(PROCESSED / 'voos_selecionados.parquet').as_posix()}' (FORMAT PARQUET)")

# Função principal que executa as etapas na ordem correta, registrando informações no log.
def main() -> None:
    con = duckdb.connect()
    ler_bruto(con)
    contar(con, 'bruto', 'Registros brutos')
    filtrar_e_limpar(con)
    criar_variaveis(con)
    separar_e_criar_alvo(con)
    selecionar_aeroportos(con)
    salvar(con)

# Executa a função principal se o script for executado diretamente, configurando o log para exibir informações detalhadas.    
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
    main()