FROM python:3.11

RUN apt-get update && apt-get install -y git

WORKDIR /app

COPY requirements.txt /app/

RUN pip install --no-cache-dir -r requirements.txt

COPY . /app/

CMD ["python", "main.py"]