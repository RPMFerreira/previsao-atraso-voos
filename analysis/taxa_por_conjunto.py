from pathlib import Path
import duckdb

RAIZ = Path(__file__).resolve().parent.parent
PARQUET = (RAIZ / 'data' / 'processed' / 'voos.parquet').as_posix()

# Mostra a quantidade de voos e o percentual de voos atrasados por conjunto (treino, validação, teste).
duckdb.sql(f"""
    SELECT conjunto, count(*) AS voos,
           round(avg(atrasado) * 100, 1) AS pct_atrasados
    FROM '{PARQUET}'
    GROUP BY conjunto ORDER BY conjunto
""").show()

# Comando utilizado para selecionar os aeroportos mais relevantes no conjunto de treino, 
# mostrando a quantidade de voos realizados por cada aeroporto.
duckdb.sql(f"""
    SELECT origem, count(*) AS voos
    FROM '{PARQUET}'
    WHERE conjunto = 'treino'
    GROUP BY origem ORDER BY voos DESC LIMIT 25
""").show(max_rows=25)

