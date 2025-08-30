FROM python:3.9-slim

RUN apt-get update && apt-get install -y entr

ENV PYTHONPATH="/app"
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src ./src

CMD ["python -m src.main"]
