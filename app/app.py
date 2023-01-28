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
from datetime import datetime, timedelta
import psycopg2
import os
import sys

#Configurações logging
logging.basicConfig(level=logging.INFO, encoding='utf-8', format="%(asctime)s - %(levelname)s - %(message)s", filename='generated_files/logs.log')


def setup_browser():
    
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    service = Service(ChromeDriverManager().install())
    browser = webdriver.Chrome(options=options, service=service)
    return browser


def create_movies_list(url):

    # acessando a pagina
    try:
        r = requests.get(url)
        r.raise_for_status()
        soup = BeautifulSoup(r.content, 'html.parser')
        table = soup.find('tbody', {'class': 'lister-list'})

        if not table:
            raise ValueError('Tabela com a class "Lister-list" não encontrada.')
        
        # selecionando todas as linhas da tabela
        all_movies = table.find_all('tr')

    # Capturando possiveis erros na conexão com a URL
    except requests.exceptions.HTTPError as errh:
        logging.warning("HTTP Error:",errh)
    except requests.exceptions.ConnectionError as errc:
        logging.warning("Error Connecting:",errc)
    except requests.exceptions.Timeout as errt:
        logging.warning("Timeout Error:",errt)
    except requests.exceptions.RequestException as err:
        logging.warning("OOps: Something Else",err)

    # Iniciando array para armazenamento dos filmes e posteriormente criação do dataframe
    data = []

    for row in all_movies:
        movie_data = row.find_all('td')
        
        # pegando valores da linha
        movie = {
            'movie_rank': movie_data[1].text.strip().split(".")[0],
            'movie_name': movie_data[1].find('a').text,
            'movie_year': movie_data[1].find('span').text.replace('(','').replace(')',''),
            'movie_imdb_rating': movie_data[2].text.replace('\n', ''),
            'movie_img_scr': movie_data[0].find('img')['src']
        }
        
        # adicionando o dict a lista de filmes
        data.append(movie)
        logging.info(f'Filme "{movie["movie_name"]}" cadastrado com sucesso.')


    # verificando se o lista dos filmes esta vazia
    if not data:
        logging.fatal('Nenhum dado recebido.')
        return
    
    # Verificando se o numero de filmes esta correto
    if len(data) != 250:
        logging.error('Numero de filmes diferente de 250.')
        return

    logging.info("Todos os dados recebidos!")   
        
    return data


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
    # Cria arquivo json e retorna o resultado
    with open("generated_files/json_movies.json", "w+") as outfile:
        json.dump(data, outfile, indent = 4)
        outfile.seek(0)
        json_data = json.load(outfile)
        print(json.dumps(json_data, indent=4))
        logging.info('Arquivo JSON Gerado com sucesso')


def create_csv_file(df):
    df.to_csv('generated_files/csv_movies.csv', index=False)
    logging.info('Arquivo CSV Gerado com sucesso')


def get_screenshot(url, path):
    
    browser = setup_browser()
    browser.get(url)
    browser.save_screenshot(path)
    browser.quit
    logging.info('Prova de consulta completa') 


def get_schedule():
    while True:
        try:
            # pega o input do usuário para o dia
            input_day = input("Insira uma data para a execução do script (DD/MM/YYYY): ")
            
            # pega o input do usuário para a hora
            input_time = input("Insira uma hora para a execução do script (HH:MM): ")
            
            # converte o input do usuário em um objeto datetime
            scheduled_date = datetime.strptime(input_day, "%d/%m/%Y")
            scheduled_time = datetime.strptime(input_time, "%H:%M").time()
            scheduled_datetime = datetime.combine(scheduled_date, scheduled_time)
            
            # verifica se a data agendada é válida
            now = datetime.now()
            if scheduled_datetime <= now:
                print("A data agendada é inválida. Por favor, insira uma data no futuro.")
                continue
                
            # verifica se a hora agendada é válida
            if scheduled_datetime.date() == now.date() and scheduled_datetime.time() <= now.time():
                print("A hora agendada é inválida. Por favor, insira uma hora no futuro.")
                continue
            
            # Obtendo a diferença entre a data atual e a data de execução
            delta_time = scheduled_datetime - now
            
            # Agendando a execução da função
            schedule.every(delta_time.total_seconds()).seconds.do(main)      
                                
            logging.info(f'Agendamento de execução para {scheduled_datetime}')
        
            break
        
        except ValueError:
            print("Data ou hora inválida. Por favor, insira novamente no formato correto (DD/MM/YYYY e HH:MM).")
            continue
     

def save_database(data):
    
    DATABASE_HOST = os.environ.get('DATABASE_HOST')
    DATABASE_NAME = os.environ.get('DATABASE_NAME')
    DATABASE_USER = os.environ.get('DATABASE_USER')
    DATABASE_PASSWORD = os.environ.get('DATABASE_PASSWORD')
    DATABASE_PORT = os.environ.get('DATABASE_PORT')

    conn = psycopg2.connect(
        host=DATABASE_HOST,
        database=DATABASE_NAME,
        user=DATABASE_USER,
        password=DATABASE_PASSWORD,
        port=DATABASE_PORT
    )
    
    
    cursor = conn.cursor()
    
    # verificando se existe a tabela movies no banco, se não, cria a mesma
    cursor.execute("SELECT to_regclass('movies')") 
    result = cursor.fetchone()  
    if not result[0]:
        
        # criando tabela
        cursor.execute("""
            CREATE TABLE movies (
                movie_rank INTEGER PRIMARY KEY NOT NULL,
                movie_name VARCHAR(255) NOT NULL,
                movie_year INTEGER NOT NULL,
                movie_imdb_rating REAL NOT NULL,
                movie_img_scr VARCHAR(255) NOT NULL
            )
        """)
        
        # Inserindo dados dos filmes
        cursor.executemany("INSERT INTO movies (movie_rank, movie_name, movie_year, movie_imdb_rating, movie_img_scr) VALUES (%(movie_rank)s, %(movie_name)s, %(movie_year)s, %(movie_imdb_rating)s, %(movie_img_scr)s)", data)
    
        
    else:
        
        # Caso a tabela ja exista apenas atualiza filmes do ranking.    
        query = "UPDATE movies SET movie_name = %(movie_name)s, movie_year = %(movie_year)s, movie_imdb_rating = %(movie_imdb_rating)s, movie_img_scr = %(movie_img_scr)s WHERE movie_rank = %(movie_rank)s"     
        cursor.executemany(query, data)
    
       
    # Salvando alterações    
    conn.commit()
    logging.info('Dados inseridos no banco de dados!')
    
    # Fechando conexão com banco
    cursor.close()   
    conn.close()
    
    
def main():
    
    logging.info('Iniciando execução.')
    
    #definindo url
    url = 'https://www.imdb.com/chart/top/?ref_=nv_mv_250'
    
    # Gerando lista dos filmes
    data = create_movies_list(url)
    
    # Criação do DataFrame com os dados da lista   
    df = create_dataframe(data)
    
    # Criação do arquivo JSON
    create_json_file(data)

    # Criação do arquivo CSV
    create_csv_file(df)

    # Prova de consulta
    get_screenshot(url, 'generated_files/prova_de_consulta.png')
    
    # Amazenamento de dados no banco de dados utilizado Postgresql
    save_database(data)

    # Final de execução
    logging.info('Execução Completa')
    return schedule.CancelJob
    

if __name__ == "__main__":
    
    get_schedule()  
    while True:       
        schedule.run_pending()    
        if not schedule.jobs:
            break 
        time.sleep(1)
    
        

            
