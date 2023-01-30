# Desafio Crawler:

Nesta fork consegui desenvolver todas as etapas do desafio proposto pela BeeMôn.

A URL escolhida foi esta:

- [imdb.com](https://www.imdb.com/chart/top/?ref_=nv_mv_250)

### Tarefas realizadas:

- :heavy_check_mark: Buscar dados de forma automatizada(script de linha de comando ou interface clicavel)
- :heavy_check_mark: Padronizar os retornos de forma estruturada (json/csv)
- :heavy_check_mark: Sistema de logs de para acompanhamento da execução
- :heavy_check_mark: Ter um prova da consulta (Screenshot)
- :heavy_check_mark: Armazenamento dos resultados em um banco relacional ou não relacional
- :heavy_check_mark: Fazer um dataframe que possibilite visualizar os resultados via pandas
- :heavy_check_mark: Trazer resultados de forma dinamica sem fixar caminhos no `xpath`
- :heavy_check_mark: Dockerizar a aplicação
- :heavy_check_mark: Conseguir agendar uma execução para um dia e horario.


### Para execução dos testes:

- Digite o comando 'python -m venv venv' para criar uma maquina virtual para o projeto

- Digite o comando 'pip install -r requirements.txt' para download das bibliotecas necessárias.

- No seu editor de texto do projeto, no terminal digite o comando 'pytest'


### Para execução do crawler:

- Será necessario a instalação do Docker na maquina

- [Windows](https://docs.docker.com/desktop/install/windows-install/)
- [Linux](https://docs.docker.com/engine/install/ubuntu/)

- No seu editor de texto, no terminal digite o comando 'docker-compose run crawler-beemon', este comando irá realizar o build das imagens do postgresql e o script do crawler então irá iniciar os containers posgres1 e desafio-crawler-crawler-beemon para iniciar a execução. Este comando já irá instalar todos os requisitos para o correto funcionamento do sistema.

- No inicio da execução serão solicitadas uma data e hora para execução do crawler.

- Durante a execução serão exibidos no terminal ou nos logs do container o DataFrame gerado e logo após a resposta Json.

- No final da execução será solicitada uma nova data e hora para execução do crawler.


### Pós execução do crawler:

- Todos os arquivos gerados na execução estarão dentro do diretório generated_files/

- Para o download dos arquivos, no seu terminal digite o comando 'docker ls', copie o name do container com a imagem 'desafio-crawler-crawler-beemon' após isso digite o comando 'docker container cp (NAME COPIADO):/app/generated_files .', este comando irá fazer o download da pasta com todos os arquivos gerados para o seu diretório local.

- Os arquivos são gerados com datas mantendo o historico de cada verificação.

- Os logs de todas as execuções são armazenados no arquivo logs.log dentro deste diretorio.

- Dentro deste diretorio e de suas respectivas pastas estarao os arquivos gerados ( json_file, csv_file e prova_de_consulta)

- Para Consultar os dados inseridos no Postgres da aplicação no terminal digite 'docker ps' e pegue o CONTAINER ID do postgres

- Após digite 'docker exec -it (CONTAINER ID) psql -U postgres -d imdbcrawler'

- Com isso para consultar os dados da tabela movies digite 'SELECT * FROM movies ORDER BY movie_rank;'


