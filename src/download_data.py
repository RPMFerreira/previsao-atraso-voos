from urllib.parse import quote
from pathlib import Path
import requests
import logging

log = logging.getLogger(__name__)

RAIZ = Path(__file__).resolve().parent.parent
PASTA = RAIZ / 'data' / 'raw'
TAMANHO_MINIMO = 10_000  # tamanho mínimo do arquivo em bytes para considerar o download válido
COLUNA_ESPERADA = 'ICAO Empresa Aérea'  # coluna esperada no arquivo CSV para validar o download

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

def validar_arquivo(caminho: Path) -> bool:
    if caminho.stat().st_size < TAMANHO_MINIMO:
        return False
    with open(caminho, encoding='utf-8-sig') as f:
        f.readline()
        cabecalho = f.readline()
    return COLUNA_ESPERADA in cabecalho

def baixar_mes(ano: int, mes: int, pasta: Path = PASTA) -> str:
    pasta.mkdir(parents=True, exist_ok=True)
    destino = pasta / f'VRA_{ano}{mes}.csv'
    if destino.exists():
        return 'ja_existia'

    temporario = destino.with_suffix('.csv.tmp')
    try:
        resposta = requests.get(url_do_mes(ano, mes), stream=True, timeout=60)
        resposta.raise_for_status()
        with open(temporario, 'wb') as f:
            for pedaco in resposta.iter_content(chunk_size=1024 * 1024):
                f.write(pedaco)
    except requests.RequestException as e:
        log.error('Falha ao baixar %d-%02d: %s', ano, mes, e)
        temporario.unlink(missing_ok=True)
        return 'falhou'

    if not validar_arquivo(temporario):
        log.error('Arquivo de %d-%02d fora do padrão esperado.', ano, mes)
        temporario.unlink(missing_ok=True)
        return 'falhou'

    temporario.replace(destino)
    return 'baixado'

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    print(baixar_mes(2025, 9))
