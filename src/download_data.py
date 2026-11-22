from urllib.parse import quote
from pathlib import Path
import requests
import logging
import time
from collections import Counter

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

# Confere se o arquivo baixado é válido, verificando tamanho e presença de cabeçalho esperado
def validar_arquivo(caminho: Path) -> bool:
    if caminho.stat().st_size < TAMANHO_MINIMO:
        return False
    with open(caminho, encoding='utf-8-sig') as f:
        f.readline()
        cabecalho = f.readline()
    return COLUNA_ESPERADA in cabecalho

# Função que baixa o arquivo CSV do VRA da ANAC para o ano e mês especificados, salvando na pasta de dados brutos
def baixar_mes(ano: int, mes: int, pasta: Path = PASTA) -> str:
    # Devolve 'baixado', 'existia' ou 'falhou'
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
    megabytes = destino.stat().st_size / (1024 * 1024)
    log.info('Baixado %d-%02d: %.1f MB', ano, mes, megabytes)
    return 'baixado'

def baixar_intervalo(ano_ini: int, mes_ini: int, ano_fim: int, mes_fim: int) -> Counter:
    if (ano_ini, mes_ini) > (ano_fim, mes_fim):
        raise ValueError('Intervalo inválido: o início é posterior ao fim.')
    
    resultados = Counter()
    falhas = []
    for ano in range(ano_ini, ano_fim + 1):
        for mes in range(1, 13):
            if (ano == ano_ini and mes < mes_ini) or (ano == ano_fim and mes > mes_fim):
                continue
            resultado = baixar_mes(ano, mes)
            resultados[resultado] += 1
            if resultado == 'falhou':
                falhas.append(f'{ano}-{mes:02d}')
            if resultado == 'baixado':
                time.sleep(1)  # evitar sobrecarga no servidor da ANAC

    log.info('Baixados: %d, Existiam %d, Falhas: %d', resultados['baixado'], resultados['ja_existia'], resultados['falhou'])
    if falhas:
        log.warning('Falhas nos meses: %s', ', '.join(falhas))

    return resultados

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(name)s: %(message)s')
    baixar_intervalo(2025, 11, 2026, 2)
