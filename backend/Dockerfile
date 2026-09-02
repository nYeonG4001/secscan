FROM python:3.14-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN groupadd --system secscan \
    && useradd --system --gid secscan --create-home --home-dir /home/secscan secscan \
    && mkdir -p /var/lib/secscan/storage \
    && chown -R secscan:secscan /var/lib/secscan /app

EXPOSE 8000
USER secscan
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
