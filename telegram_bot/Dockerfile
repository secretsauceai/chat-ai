FROM python:3.10-slim-buster

RUN mkdir /app
WORKDIR /app

COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

COPY ./telegram_bot.py .

CMD ["python", "telegram_bot.py"]
