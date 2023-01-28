from app.app import get_request

def test_get_request_success():
    url = 'https://www.imdb.com/chart/top/?ref_=nv_mv_250'
    r = get_request(url)
    assert r.status_code == 200

