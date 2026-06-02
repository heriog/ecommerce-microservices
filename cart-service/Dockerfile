FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system deps
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Create app user
RUN useradd --create-home appuser
WORKDIR /home/appuser

# Copy requirements and install
COPY requirements.txt /home/appuser/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY app /home/appuser/app
RUN chown -R appuser:appuser /home/appuser

USER appuser

EXPOSE 8000

# Use Gunicorn to serve the Flask app in production
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8000", "app.main:app", "--log-level", "info"]
