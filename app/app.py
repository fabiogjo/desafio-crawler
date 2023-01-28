from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
import requests
from bs4 import BeautifulSoup
import json
import logging
import schedule
import time
from datetime import datetime
import psycopg2
import os
import traceback

GENERATED_FILES_PATH = 'generated_files'



#Configurações logging
logging.basicConfig(level=logging.INFO, encoding='utf-8', format="%(asctime)s - %(levelname)s - %(message)s", filename=f'{GENERATED_FILES_PATH}/logs.log')


def setup_browser():
    
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    service = Service(ChromeDriverManager().install())
    browser = webdriver.Chrome(options=options, service=service)
    return browser


def get_request(url):

    # acessando a pagina
    try:
        r = requests.get(url)
        r.raise_for_status()
        return r

    # Capturando possiveis erros na conexão com a URL
    except requests.exceptions.HTTPError as errh:
        logging.warning("HTTP Error:",errh)
        raise errh
    except requests.exceptions.ConnectionError as errc:
        logging.warning("Error Connecting:",errc)
    except requests.exceptions.Timeout as errt:
        logging.warning("Timeout Error:",errt)
    except requests.exceptions.RequestException as err:
        logging.warning("OOps: Something Else",err)


def get_table_body_rows(content, identifier):

    soup = BeautifulSoup(content, 'html.parser')

    table = soup.find('tbody', identifier)

    if not table:
        raise ValueError('Tabela não encontrada.')
        
    # selecionando todas as linhas da tabela
    rows = table.find_all('tr')

    return rows


def create_movies_list(table_rows):

    # Iniciando array para armazenamento dos filmes e posteriormente criação do dataframe
    data = []

    for table_row in table_rows:
        movie_data = table_row.find_all('td')

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
    
    return df


def create_json_file(data, date):

    # Cria arquivo json
    with open(f"{GENERATED_FILES_PATH}/json_movies_{date}.json", "w+", encoding='utf-8') as outfile:
        json.dump(data, outfile, indent = 4)

        #exibindo o resultado
        outfile.seek(0)
        json_data = json.load(outfile)
        logging.info('Arquivo JSON Gerado com sucesso')
        return json.dumps(json_data, indent=4)


def create_csv_file(df, date):
    df.to_csv(f'{GENERATED_FILES_PATH}/csv_movies_{date}.csv', index=False)
    logging.info('Arquivo CSV Gerado com sucesso')


def make_screenshot(url, path):
    
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
    else:
        cursor.execute("DELETE FROM movies")


    # Inserindo dados dos filmes
    cursor.executemany("INSERT INTO movies (movie_rank, movie_name, movie_year, movie_imdb_rating, movie_img_scr) VALUES (%(movie_rank)s, %(movie_name)s, %(movie_year)s, %(movie_imdb_rating)s, %(movie_img_scr)s)", data)
    
       
    # Salvando alterações    
    conn.commit()
    logging.info('Dados inseridos no banco de dados!')
    
    # Fechando conexão com banco
    cursor.close()   
    conn.close()
    
    
def main():
    
    now = datetime.now()
    start_date = now.strftime("%Y-%m-%d-%H-%M-%S-%f")

    logging.info('Iniciando execução.')
    
    #definindo url
    url = 'https://www.imdb.com/chart/top/?ref_=nv_mv_250'

    try:
        # Acessando URL
        request = get_request(url)

        # Retorna todas as linhas da tabela
        table_rows = get_table_body_rows(request.content, {'class': 'lister-list'})

        # Gerando lista dos filmes
        data = create_movies_list(table_rows)
        
        # Criação do DataFrame com os dados da lista   
        df = create_dataframe(data)
        print(df)
        
        # Criação do arquivo JSON
        json_dump = create_json_file(data, start_date)
        print(json_dump)

        # Criação do arquivo CSV
        create_csv_file(df, start_date)

        # Prova de consulta
        make_screenshot(url, f'{GENERATED_FILES_PATH}/prova_de_consulta_{start_date}.png')
        
        # Amazenamento de dados no banco de dados utilizado Postgresql
        save_database(data)

        # Final de execução
        logging.info('Execução Completa')
        return schedule.CancelJob


    except requests.exceptions.RequestException as err:
        logging.fatal(f'Request fail! {errh} {type(errh)}')
    except Exception as errh:
        traceback.print_exc()
        logging.fatal(f'Something wrong! {errh} {type(errh)}')
   

if __name__ == "__main__":
    
    get_schedule()  
    while True:       
        schedule.run_pending()    
        if not schedule.jobs:
            get_schedule() 
        time.sleep(1)


            
