# Teste do funcionamento da função url_do_mes() do módulo download_data.py
from src.download_data import url_do_mes
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
    import pytest
    with pytest.raises(ValueError):
        url_do_mes(2025, 13)