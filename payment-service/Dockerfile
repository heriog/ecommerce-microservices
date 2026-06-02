FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential libpq-dev \
    && rm -rf /var/lib/apt/lists/*
RUN useradd --create-home appuser
WORKDIR /home/appuser
COPY requirements.txt /home/appuser/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY app /home/appuser/app
RUN chown -R appuser:appuser /home/appuser
USER appuser
EXPOSE 8000
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8000", "app:create_app()", "--log-level", "info"]
