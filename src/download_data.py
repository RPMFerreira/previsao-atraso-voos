from urllib.parse import quote

# Estrutura básica do site da ANAC para download de dados abertos
BASE = 'https://sistemas.anac.gov.br/dadosabertos/'
CAMINHO = 'Voos e operações aéreas/Voo Regular Ativo (VRA)'
MESES = {
    1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril',
    5: 'Maio', 6: 'Junho', 7: 'Julho', 8: 'Agosto',
    9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro',
}

# Função que gera a URL para download do arquivo CSV do VRA (Voo Regular Ativo) da ANAC
def url_do_mes(ano: int, mes: int) -> str:
    if mes not in MESES:
        raise ValueError(f'Mês inválido: {mes}.')
    arquivo = f'VRA_{ano}{mes}.csv'           # sem zero: 9 -> VRA_20269
    pasta = f'{mes:02d} - {MESES[mes]}'      # confirmar se a pasta usa zero
    caminho = f'{CAMINHO}/{ano}/{pasta}/{arquivo}'
    return BASE + quote(caminho)