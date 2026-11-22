# Teste do funcionamento das funções url_do_mes() e validar_arquivo() do módulo download_data.py
from src.download_data import url_do_mes, validar_arquivo, baixar_intervalo
import pytest

def test_url_dezembro_2025():
    esperado = ('https://sistemas.anac.gov.br/dadosabertos/'
                'Voos%20e%20opera%C3%A7%C3%B5es%20a%C3%A9reas/'
                'Voo%20Regular%20Ativo%20%28VRA%29/2025/'
                '12%20-%20Dezembro/VRA_202512.csv')
    assert url_do_mes(2025, 12) == esperado

def test_url_mes_de_um_digito():
    esperado = ('https://sistemas.anac.gov.br/dadosabertos/'
                'Voos%20e%20opera%C3%A7%C3%B5es%20a%C3%A9reas/'
                'Voo%20Regular%20Ativo%20%28VRA%29/2026/'
                '09%20-%20Setembro/VRA_20269.csv')
    assert url_do_mes(2026, 9) == esperado

def test_mes_invalido():
    with pytest.raises(ValueError):
        url_do_mes(2025, 13)

def test_validar_arquivo_ok(tmp_path):
    arq = tmp_path / 'x.csv'
    arq.write_text(
        'Atualizado em: 2026-01-01\n'
        '"ICAO Empresa Aérea";"Número Voo"\n' + 'x' * 20000,
        encoding='utf-8',
    )
    assert validar_arquivo(arq)


def test_validar_arquivo_pequeno(tmp_path):
    arq = tmp_path / 'x.csv'
    arq.write_text('erro', encoding='utf-8')
    assert not validar_arquivo(arq)


def test_validar_arquivo_sem_cabecalho(tmp_path):
    arq = tmp_path / 'x.csv'
    arq.write_text(
        'Atualizado em: 2026-01-01\n'
        '<html>Pagina de erro</html>\n' + 'x' * 20000,
        encoding='utf-8',
    )
    assert not validar_arquivo(arq)

def test_intervalo_cruza_virada_de_ano(monkeypatch):
    chamados = []

    def falso_baixar_mes(ano, mes):
        chamados.append((ano, mes))
        return 'baixado'

    monkeypatch.setattr('src.download_data.baixar_mes', falso_baixar_mes)
    monkeypatch.setattr('src.download_data.time.sleep', lambda s: None)

    resultados = baixar_intervalo(2025, 11, 2026, 2)

    assert chamados == [(2025, 11), (2025, 12), (2026, 1), (2026, 2)]
    assert resultados['baixado'] == 4