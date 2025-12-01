# bot/Dockerfile

FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

ENV PATH="/app/.venv/bin:${PATH}"

COPY . ./bot/

ENV PYTHONPATH="/app:$PYTHONPATH"

CMD ["python", "bot/main.py"]
