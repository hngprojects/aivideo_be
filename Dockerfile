# Use an official Python runtime as the base image
FROM python:3.12.4-slim-bullseye

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Set the working directory in the container
WORKDIR /app

# Install system dependencies (optional, if needed)
# RUN apk add --no-cache curl

# Copy the requirements.txt file and install with pip
COPY ./requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --upgrade -r requirements.txt

# Copy the rest of the backend files
COPY . /app/

# Download wait-for-it script
ADD https://raw.githubusercontent.com/vishnubob/wait-for-it/master/wait-for-it.sh /usr/local/bin/wait-for-it.sh
RUN chmod +x /usr/local/bin/wait-for-it.sh

# Expose the port the app runs on
EXPOSE 7001

# Command to run the application with wait-for-it to ensure RabbitMQ is ready
CMD ["sh", "-c", "./wait-for-it.sh rabbitmq:5672 -- uvicorn main:app --host 0.0.0.0 --port 7001 --reload"]
