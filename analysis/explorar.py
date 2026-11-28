from pathlib import Path
import duckdb
import matplotlib.pyplot as plt

RAIZ = Path(__file__).resolve().parent.parent
PARQUET = (RAIZ / 'data' / 'processed' / 'voos_selecionados.parquet').as_posix()
FIGURAS = RAIZ / 'docs' / 'figuras'
DIAS = {1: 'Seg', 2: 'Ter', 3: 'Qua', 4: 'Qui', 5: 'Sex', 6: 'Sab', 7: 'Dom'}

def taxa_por(coluna: str):
    return duckdb.sql(f"""
        SELECT {coluna} AS grupo, count(*) AS voos,
               round(avg(atrasado) * 100, 1) AS pct_atrasados
        FROM '{PARQUET}'
        WHERE conjunto = 'treino'
        GROUP BY {coluna} 
        HAVING count(*) >= 1000
        ORDER BY {coluna}
    """).df()

def grafico_barras(df, titulo: str, arquivo: str, media: float) -> None:
    FIGURAS.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar(df['grupo'].astype(str), df['pct_atrasados'])
    ax.axhline(media, linestyle='--', color='gray', label=f'Média do treino ({media:.1f}%)')

    ax.set_title(titulo)
    ax.set_xlabel('Grupo')
    ax.set_ylabel('Porcentagem de voos atrasados (> 15 min)')
    ax.legend()
    ax.tick_params(axis='x', rotation=45)

    fig.tight_layout()
    fig.savefig(FIGURAS / arquivo, dpi=150)
    plt.close(fig)

if __name__ == '__main__':
    media = duckdb.sql(f"""
        SELECT avg(atrasado) * 100 FROM '{PARQUET}' WHERE conjunto = 'treino'
        """).fetchall()[0][0]
    
    for coluna in ['hora_prevista', 'dia_semana', 'mes', 'empresa', 'origem']:
        df = taxa_por(coluna)
        if coluna == 'dia_semana':
            df['grupo'] = df['grupo'].map(DIAS)
        print(df.to_string(index=False))
        grafico_barras(df, f'Taxa de atraso por {coluna} (treino, 2023)',
                       f'taxa_{coluna}.png', media)