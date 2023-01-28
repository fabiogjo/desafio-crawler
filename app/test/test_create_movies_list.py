import unittest
import requests
from bs4 import BeautifulSoup
from ..app import create_movies_list

class TestCreateMoviesList(unittest.TestCase):

    def test_valid_url(self):
        # Testa se a função create_movies_list() retorna uma lista não vazia quando passada uma URL válida
        url = 'https://www.imdb.com/chart/top/'
        result = create_movies_list(url)
        self.assertIsNotNone(result)

    def test_invalid_url(self):
        # Testa se a função create_movies_list() retorna uma lista não vazia quando passada uma URL válida
        url = 'https://www.imdb.com/chart444/top/'
        r = requests.get(url)
        self.assertNotEqual(r.status_code, 200)

    def test_correct_number_of_movies(self):
        # Testa se a função create_movies_list() retorna uma lista com 250 elementos
        url = 'https://www.imdb.com/chart/top/'
        result = create_movies_list(url)
        self.assertEqual(len(result), 250)

    def test_status_code(self):
        # Testa se a url retorna um status code 200
        url = 'https://www.imdb.com/chart/top'
        r = requests.get(url)
        self.assertEqual(r.status_code, 200)

    def test_html_parser(self):
        # Testa se o html.parser esta funcionando corretamente
        url = 'https://www.imdb.com/chart/top'
        r = requests.get(url)
        soup = BeautifulSoup(r.content, 'html.parser')
        self.assertIsNotNone(soup)

    def test_table_class(self):
        # Testa se o scrip esta encontrando a tabela corretamente
        url = 'https://www.imdb.com/chart/top'
        r = requests.get(url)
        soup = BeautifulSoup(r.content, 'html.parser')
        table = soup.find('tbody', {'class': 'lister-list'})
        self.assertIsNotNone(table)

    def test_movie_data(self):
        # Testa se o scrip esta recolhendo os dados corretamente
        url = 'https://www.imdb.com/chart/top'
        data = create_movies_list(url)
        self.assertIsNotNone(data)
        self.assertIsInstance(data, list)
        self.assertIsInstance(data[0], dict)
        self.assertIn('movie_rank', data[0])
        self.assertIn('movie_name', data[0])
        self.assertIn('movie_year', data[0])
        self.assertIn('movie_imdb_rating', data[0])
        self.assertIn('movie_img_scr', data[0])

if __name__ == '__main__':
    unittest.main()