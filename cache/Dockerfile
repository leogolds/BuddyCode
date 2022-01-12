FROM tiangolo/uvicorn-gunicorn:python3.8-slim

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1

# Install pip requirements
COPY ./cache/requirements.txt .
RUN python -m pip install -r requirements.txt

COPY ./cache /app
COPY ./common /app/common
