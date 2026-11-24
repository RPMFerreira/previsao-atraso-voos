from pathlib import Path
import duckdb

RAIZ = Path(__file__).resolve().parent.parent
PARQUET = (RAIZ / 'data' / 'processed' / 'voos.parquet').as_posix()

duckdb.sql(f"""
    SELECT conjunto, count(*) AS voos,
           round(avg(atrasado) * 100, 1) AS pct_atrasados
    FROM '{PARQUET}'
    GROUP BY conjunto ORDER BY conjunto
""").show()
