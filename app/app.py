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
import psycopg2

#Configurações logging
logging.basicConfig(level=logging.INFO, encoding='utf-8', filename='generated_files/logs.log', format="%(asctime)s - %(levelname)s - %(message)s")


def setup_browser():

    options = webdriver.ChromeOptions()

    options.add_argument("--headless")

    service = Service(ChromeDriverManager().install())

    browser = webdriver.Chrome(options=options, service=service)

    return browser


def create_dataframe(data):
    
    # Criando dataframe
    df = pd.DataFrame(data)

    # alterando a coluna index
    df.reset_index(drop=True, inplace=True)

    # verificando se o dataframe foi gerado corretamente
    if df.empty:
        logging.fatal('DataFrame nao gerado')
        return

    # exibindo DataFrame
    print(df)
    
    return df
    

def create_json_file(data):
    with open("generated_files/json_movies.json", "w") as outfile:
        json.dump(data, outfile, indent = 4)


def create_movies_list(data, movies_array):
    
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

        # criando um dict com os dados do filme
        movie = {
                
            'movie_rank': movie_rank,
                
            'movie_name': movie_name,

            'movie_year': movie_year,
                
            'movie_imdb_rating': movie_imdb_rating,
                
            'movie_img_scr': movie_img_scr
                
        }
        
        # adicionando o dict a lista de filmes
        data.append(movie)
        
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
    
    logging.info(f'Agendamento de execução para {scheduled_datetime}')
    
    return scheduled_datetime
    

def save_database(data):
    
    # criando coneção com o banco de dados
    conn = psycopg2.connect(
        
        host="localhost",
        database="imdbcrawler",
        user="postgres",
        password="123456",
        port="5432"
        
    )
    
    cursor = conn.cursor()
    
    # verificando se existe a tabela movies no banco, se não, cria a mesma
    cursor.execute("""
        SELECT to_regclass('movies');
    """)
    
    result = cursor.fetchone()
    
    if not result[0]:
        
        # criando tabela
        cursor.execute("""
            CREATE TABLE movies (
                id SERIAL PRIMARY KEY,
                movie_rank INTEGER NOT NULL,
                movie_name VARCHAR(255) NOT NULL,
                movie_year INTEGER NOT NULL,
                movie_imdb_rating REAL NOT NULL,
                movie_img_scr VARCHAR(255) NOT NULL
            )
        """)
        
    else:
        
        # Excluindo dados da tabela ja existente para a atualização.
        cursor.execute("DELETE FROM movies")
    
    # Inserindo dados dos filmes
    cursor.executemany("INSERT INTO movies (movie_rank, movie_name, movie_year, movie_imdb_rating, movie_img_scr) VALUES (%(movie_rank)s, %(movie_name)s, %(movie_year)s, %(movie_imdb_rating)s, %(movie_img_scr)s)", data)
       
    # Salvando alterações    
    conn.commit()
    
    # Fechando conexão com banco
    cursor.close()
    
    conn.close()
    
    
def main():

    logging.info('Iniciando execução.')
    
    #definindo url
    url = 'https://www.imdb.com/chart/top/?ref_=nv_mv_250'
    
    #iniciando lista dos dados
    data = list()
    
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
    
    # Gerando lista dos filmes
    create_movies_list(data, all_movies)
    
    # verificando se o lista dos filmes esta vazia
    if not data:
        logging.fatal('Nenhum dado recebido.')
        return

    logging.info("Todos os dados recebidos!")
    
    
    # Criação do DataFrame com os dados da lista   
    df = create_dataframe(data)
    

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
    
    
    # Amazenamento de dados no banco de dados utilizado Postgresql
    save_database(data)


    # Final de execução
    logging.info('Execução Completa')


if __name__ == "__main__":
    
    scheduled_datetime = get_schedule()
    
    # Agendar a execução do script na data e hora especificadas pelo usuário
    schedule.every().day.at(scheduled_datetime.strftime("%H:%M")).do(main)
    
    while True:
        
        schedule.run_pending()
        
        time.sleep(1)
