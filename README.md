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

### Dicionário de dados

Colunas da base VRA utilizadas no projeto:

| Coluna | Significado | Tipo | Fuso/formato | Uso no projeto |
|---|---|---|---|---|
| ICAO Empresa Aérea | Sigla ICAO (International Civil Aviation Organization) para empresas aéreas | Texto | - | Variável |
| Número Voo | Numeração do voo | Número | - | Identificador |
| Código Autorização (DI) | Caractere usado para identificar o Dígito Identificador (DI) para cada etapa de voo | Número | - | A ser investigado
| Código Tipo Linha | Caractere usado para identificar o Tipo de Linha realizada para cada etapa de voo | Texto | - | Filtro |
| ICAO Aeródromo Origem | Sigla ICAO do aeroporto de origem | Texto | - | Variável |
| ICAO Aeródromo Destino | Sigla ICAO do aeroporto de destino | Texto | - | Variável |
| Partida Prevista | Data e horário da partida prevista informada pela empresa aérea | Data | Brasília | Variável |
| Partida Real | Data e horário da partida realizada informada pela empresa aérea | Data | Brasília | Auxiliar (calcula o alvo) |
| Chegada Prevista | Data e horário da chegada prevista informada pela empresa aérea | Data | Brasília | Variável (a ser descartada) |
| Chegada Real | Data e horário da chegada realizada informada pela empresa aérea | Data | Brasília | Variável (a ser descartada) |
| Situação Voo | Campo informando a situação do voo: realizado, cancelado ou não informado | Texto | - | Filtro |
| Código Justificativa | Este campo deixou de ser exigido a partir de abril de 2020, com a revogação da Instrução de Aviação Civil (IAC) 1504 | Texto | - | Descartada |

#### Regras adotadas

- **Fuso Horário:** todos os horários da base estão no horário de Brasília [fonte: metadados do VRA da ANAC]. Nenhuma conversão foi necessária.
- **Definição de atraso:** a ANAC não fixa oficialmente um tempo de diferença entre horário de partida prevista e horário de partida real como atraso. Contudo, o padrão adotado internacionalmente é de 15 minutos. A Seção § 234.2 (Definitions) do Title 14 CFR Part 234 (Departamento de Transportes dos EUA — DOT) define textualmente o termo Late or late flight (voo atrasado) como qualquer voo que chegue ao portão 15 minutos ou mais após o horário de chegada publicado. O indicador OTP15 da EUROCONTROL / Cirium / OAGO classifica como pontual o voo que chega ou parte em até 15 minutos após o horário programado (sendo considerado atrasado a partir de 15 minutos e 1 segundo). Portanto, alvo `atrasado` vale 1 quando o tempo de diferença entre horário de partida prevista e horário de partida real é maior que 15 minutos e 0 caso contrário.
- **Voos cancelados:** excluídos e tratados a parte, visto que o alvo não existe para eles, não há horários de partida previstos e reais para serem considerados.
- **Voos sem horário previsto:** excluídos, porque sem ele não é possível medir atraso.
- **Número do voo:** tratado como texto, pois há valores com letras. Não é usado como variável na primeira versão.
- **Duplicados:** removidos pela combinação companhia, número do voo, origem e partida prevista.
- **Formato do arquivo:** a primeira linha contém a data de atualização e é ignorada na leitura. Separador `;`, valores ausentes como `null`.

#### Códigos usados

- **Código Tipo Linha:** 'N' = Doméstica Mista, 'I' = Internacional Mista.
- **Código Autorização (DI):** '0' = Etapa Regular, '2' = Etapa Extra, '4' = Inclusão de Etapa, 'D' = Etapa de Voo Duplicada.
- 
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
