FROM python:3.9

WORKDIR /app

COPY requirements.txt .

RUN pip install -r requirements.txt --no-cache-dir

COPY entrypoint.sh /app/entrypoint.sh

RUN chmod +x /app/entrypoint.sh

COPY . .

ENTRYPOINT ["/app/entrypoint.sh"]

CMD ["gunicorn", "--bind", "0.0.0.0:8080", "config.wsgi"]


# FROM python:3.9

# WORKDIR /app

# COPY requirements.txt .

# RUN pip install -r requirements.txt --no-cache-dir

# COPY . .

# CMD ["gunicorn", "--bind", "0.0.0.0:8080", "config.wsgi"]