from pathlib import Path
import pandas as pd
from sklearn.metrics import roc_auc_score, brier_score_loss

RAIZ = Path(__file__).resolve().parent.parent
PARQUET = RAIZ / 'data' / 'processed' / 'voos_selecionados.parquet'

df = pd.read_parquet(PARQUET)
treino = df[df['conjunto'] == 'treino']
validacao = df[df['conjunto'] == 'validacao']
y = validacao['atrasado']

taxa_global = treino['atrasado'].mean()

previsoes = {
    'Constante (taxa global)': pd.Series(taxa_global, index=validacao.index),
    'Taxa por rota': validacao['rota'].map(treino.groupby('rota')['atrasado'].mean()),
    'Taxa por hora': validacao['hora_prevista'].map(treino.groupby('hora_prevista')['atrasado'].mean()).fillna(taxa_global),
}

for nome, p in previsoes.items():
    print(f'{nome:28s} nulos={p.isna().sum()}  '
          f'AUC={roc_auc_score(y, p):.3f}  Brier={brier_score_loss(y, p):.5f}')