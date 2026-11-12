# Previsão de atraso de voos no Brasil

Estimativa da probabilidade de atraso de voos domésticos a partir de dados públicos da ANAC, com avaliação rigorosa do modelo, API REST e, futuramente, um agente que explica o resultado em linguagem simples.

> **Status: em desenvolvimento.** Este README é atualizado a cada etapa.

## Qual decisão este projeto ajuda

Quem vai comprar uma passagem ou escolher o tempo de espera entre dois voos precisa saber qual é o risco de atraso. O projeto estima essa probabilidade usando **apenas informações que existem antes do voo** (rota, companhia, horário, dia da semana e época do ano).

## Dados

- **Fonte:** base VRA (Voo Regular Ativo), da ANAC, com horários previstos e realizados dos voos.
- **Período:** 2023 a 2025, dividido por data:
  - Treino: 2023
  - Validação (ajuste do modelo): 2024
  - Teste final: 2025
- **Exclusão:** 2020 a 2022, por causa dos efeitos da pandemia e da retomada do setor aéreo. *(Hipótese a confirmar nos dados.)*
- **Seleção de aeroportos e rotas** (regra definida antes de olhar o resultado):
  1. Contar os voos por aeroporto apenas no período de treino.
  2. Manter os aeroportos com mais voos [N a definir].
  3. Manter as rotas entre eles com pelo menos [mínimo a definir] voos no treino.
- **Lista final de aeroportos e contagens:** *a preencher após a etapa de limpeza.*
- Os dados **não** estão neste repositório. Veja "Como rodar" para baixá-los.

## Principais decisões de modelagem

- **Divisão por data, e não aleatória:** o modelo treina com o passado e é testado com o futuro, como seria na prática.
- **Sem vazamento de dados:** nenhuma informação obtida depois do voo entra como variável.
- **Comparação com uma linha de base** (taxa histórica de atraso da rota): um modelo só vale se superá-la.
- **Calibração das probabilidades:** quando o modelo diz 30%, cerca de 30% dos voos devem atrasar.

## Resultados

*Em construção.*

| Modelo | ROC-AUC | Brier score |
|---|---|---|
| Linha de base (média histórica) | – | – |
| Regressão logística | – | – |
| Gradient boosting | – | – |

## Tecnologias

Python · DuckDB · pandas · scikit-learn · FastAPI · PostgreSQL · pytest · GitHub Actions

## Roadmap

- [ ] Obtenção e limpeza dos dados
- [ ] Análise exploratória e linha de base
- [ ] Modelagem e avaliação
- [ ] Banco de dados PostgreSQL
- [ ] API REST (FastAPI)
- [ ] Testes automatizados e CI
- [ ] Agente conversacional (opcional)

## Como rodar

*Em construção.*

## Limitações

*Em construção. Será preenchida com o que o modelo não consegue prever e com os pontos fracos encontrados nos testes.*

## Aviso

As previsões são **estimativas estatísticas** baseadas em dados históricos. Não são garantia nem aconselhamento sobre compra de passagens.

## Autor

Rafael Pires de Melo Ferreira · [LinkedIn](https://www.linkedin.com/in/rafaelpmferreira/)
