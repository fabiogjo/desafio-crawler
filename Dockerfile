FROM python:3

# Add chrome and chromedriver
RUN apt-get update \
    && apt-get install -y wget gnupg \
    && wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list' \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && apt-get install -y unzip \
    && wget https://chromedriver.storage.googleapis.com/76.0.3809.68/chromedriver_linux64.zip \
    && unzip chromedriver_linux64.zip \
    && mv chromedriver /usr/bin/chromedriver \
    && chmod +x /usr/bin/chromedriver

WORKDIR /app

COPY . .

ENV TZ="America/Sao_Paulo"

RUN pip install -r requirements.txt

CMD ["python", "app/app.py"]