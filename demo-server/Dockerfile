FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

ENV PATH="/app/.venv/bin:${PATH}"

COPY . ./demo-server/

ENV PYTHONPATH="/app:$PYTHONPATH"

EXPOSE 8001

CMD ["uvicorn", "demo-server.main:app", "--host", "0.0.0.0", "--port", "8001"]