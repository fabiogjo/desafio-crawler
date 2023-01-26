from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
import requests
from bs4 import BeautifulSoup
from unidecode import unidecode
import json
import logging
import schedule
import time
import datetime

#Configurações logging
logging.basicConfig(level=logging.INFO, encoding='utf-8', filename='generated_files/logs.log', format="%(asctime)s - %(levelname)s - %(message)s")


def setup_browser():

    options = webdriver.ChromeOptions()

    options.add_argument("--headless")

    service = Service(ChromeDriverManager().install())

    browser = webdriver.Chrome(options=options, service=service)

    return browser


def create_json_file(dictionary):
    with open("generated_files/json_movies.json", "w") as outfile:
        json.dump(dictionary, outfile, indent = 4)


def create_movies_dict(data, movies_array):
    
    for row in movies_array:
            
        # pegando valores da linha
        movie_data = row.find_all('td')
            
        # ranking do filme
        movie_rank = movie_data[1].text

        dot_index = movie_rank.find('.')

        movie_rank = movie_rank[0:dot_index].replace(' ', '').replace('\n', '')
            
        # nome do filme
        movie_name = movie_data[1].find('a')

        #verificando se o nome foi encontrado corretamente
        if not movie_name:
            logging.fatal(f'Nome do filme rank: {movie_rank} nao encontrado')
            return
        
        # coletando o nome
        movie_name = movie_name.text

        # ano do filme
        movie_year = movie_data[1].find('span')

        #verificando se o ano foi encontrado corretamente
        if not movie_year:
            logging.fatal(f'Ano do filme {movie_name} nao encontrado')
            return
        
        # coletando o ano
        movie_year = movie_year.text

        # removendo os caracteres ( ) do ano 
        char_remov = ['(', ')']
        for char in char_remov:
            movie_year = movie_year.replace(char, '')
            
        # avaliação imdb
        movie_imdb_rating = movie_data[2]

        #verificando se a avaliação imdb foi encontrado corretamente
        if not movie_imdb_rating:
            logging.fatal(f'Avaliação do filme {movie_name} nao encontrada')
            return

        # coletando a avaliação e tratando o dado removendo as quebras de linhas
        movie_imdb_rating = movie_imdb_rating.text.replace('\n', '')
            
        # pegando o scr do poster do filme
        movie_img_scr = movie_data[0].find('img')['src']

        # Removendo acentuação e letras maiusculas para ser a chave do dicionario
        movie_key = unidecode(movie_name.lower())
            
        # criando um dict com os dados do filme
        data[movie_key] = {
                
            'movie_rank': movie_rank,
                
            'movie_name': movie_name,

            'movie_year': movie_year,
                
            'movie_imdb_rating': movie_imdb_rating,
                
            'movie_img_scr': movie_img_scr
                
        }
        
        logging.info(f'Filme "{movie_name}" cadastrado com sucesso.')


def get_screenshot(url, path):
    
    browser = setup_browser()

    browser.get(url)

    browser.save_screenshot(path)

    browser.quit 


def get_schedule():
    
    # pega o input do usuário para o dia
    input_day = input("Insira uma data para a execução do script (DD/MM/YYYY): ")
    
    # pega o input do usuário para a hora
    input_time = input("Insira uma hora para a execução do script (HH:MM): ")
    
    # converte o input do usuário em um objeto datetime
    scheduled_date = datetime.datetime.strptime(input_day, "%d/%m/%Y")
    scheduled_time = datetime.datetime.strptime(input_time, "%H:%M").time()
    scheduled_datetime = datetime.datetime.combine(scheduled_date, scheduled_time)
    
    return scheduled_datetime
    
    
def main():

    logging.info('Iniciando execução.')
    
    #definindo url
    url = 'https://www.imdb.com/chart/top/?ref_=nv_mv_250'
    
    #iniciando dict dos dados
    data = dict()
    
    # acessando a pagina
    r = requests.get(url)
    logging.info('Tentando conexão com URL.')
    
    # return early caso houver algum problema para acessar a URL
    if r.status_code != 200:
        logging.warning("URL não acessivel")
        return

    logging.info('URL conectada com sucesso.')
    
    # selecionando tabela a ser trabalhada
    content = r.content      
    soup = BeautifulSoup(content, 'html.parser')    
    table = soup.find('tbody', {'class': 'lister-list'})

    if not table:
        logging.fatal('Tabela com a class "Lister-list" não encontrada.')
        return
    
    # selecionando todas as linhas da tabela
    all_movies = table.find_all('tr')
    
    # Gerando dicionario dos filmes passando a variavel a ser armazenados os dados e o array de linhas da tabela
    create_movies_dict(data, all_movies)
    
    # verificando se o dicionario dos filmes esta vazio
    if not data:
        logging.fatal('Nenhum dado recebido.')
        return

    logging.info("Todos os dados recebidos!")
    

    # Criação do DataFrame com os dados do dicionario    
    df = pd.DataFrame(data).transpose()

    # alterando a coluna index
    df.reset_index(drop=True, inplace=True)

    # verificando se o dataframe foi gerado corretamente
    if df.empty:
        logging.fatal('DataFrame nao gerado')
        return

    # exibindo DataFrame
    print(df)

    # Criação do arquivo JSON
    create_json_file(data)
    logging.info('Arquivo JSON Gerado com sucesso')

    # Retorno JSON
    result = df.to_json(orient = "records")
    print(result)

    # Criação do arquivo CSV
    df.to_csv('generated_files/csv_movies.csv', index=False)
    logging.info('Arquivo CSV Gerado com sucesso')

    # Prova de consulta
    get_screenshot(url, 'generated_files/prova_de_consulta.png')

    # Final de execução
    logging.info('Execução Completa')


if __name__ == "__main__":
    
    scheduled_datetime = get_schedule()
    
    # Agendar a execução do script na data e hora especificadas pelo usuário
    schedule.every().day.at(scheduled_datetime.strftime("%H:%M")).do(main)
    
    while True:
        
        schedule.run_pending()
        
        time.sleep(1)
    
    
