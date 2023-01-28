from bs4 import BeautifulSoup
from app.app import get_table_body_rows, get_request

def test_html_parser():
    # Testa se o html.parser esta funcionando corretamente
    url = 'https://www.imdb.com/chart/top/?ref_=nv_mv_250'
    r = get_request(url)
    soup = BeautifulSoup(r.content, 'html.parser')
    assert soup is not None

def test_table_identifier():
    # Testa se o scrip esta encontrando a tabela corretamente
    url = 'https://www.imdb.com/chart/top/?ref_=nv_mv_250'
    r = get_request(url)
    rows = get_table_body_rows(r.content, {'class': 'lister-list'})
    assert rows is not None