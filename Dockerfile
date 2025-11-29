FROM python:3.11-slim

WORKDIR /app

# keep python from writing .pyc files and buffer logs
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# copy the rest of the project into the image
COPY . .

# flask configuration
ENV FLASK_APP=app
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_RUN_PORT=5000

# expose port 5000 for container
EXPOSE 5000

# start app
CMD ["python", "app.py"]
