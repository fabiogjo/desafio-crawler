from app.app import *

def test_correct_number_of_movies():
    # Testa se a função create_movies_list() retorna uma lista com 250 elementos
    url = 'https://www.imdb.com/chart/top/?ref_=nv_mv_250'
    r = get_request(url)
    table_rows = get_table_body_rows(r.content, {'class': 'lister-list'})
    result = create_movies_list(table_rows)
    assert len(result) == 250

def test_movie_data():
    # Testa se o scrip esta recolhendo os dados corretamente
    url = 'https://www.imdb.com/chart/top/?ref_=nv_mv_250'
    r = get_request(url)
    table_rows = get_table_body_rows(r.content, {'class': 'lister-list'})
    result = create_movies_list(table_rows)
    assert result is not None
    assert isinstance(result, list)
    assert isinstance(result[0], dict)
    assert 'movie_rank' in result[0]
    assert 'movie_name' in result[0]
    assert 'movie_year' in result[0]
    assert 'movie_imdb_rating' in result[0]
    assert 'movie_img_scr' in result[0]