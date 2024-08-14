# Setting Up Celery and RabbitMQ on a Linux Environment

This guide will walk you through setting up Celery and RabbitMQ on a Linux environment. Celery is a powerful, flexible distributed task queue system, and RabbitMQ is a widely used message broker that Celery can use to send and receive messages.

## Prerequisites

- A Linux-based operating system (Ubuntu/Debian, CentOS, etc.)
- Python 3.6+ installed
- Pip (Python package manager) installed
- Git installed

## Step 1: Install RabbitMQ

RabbitMQ is the message broker that Celery will use to communicate between your application and workers.

### 1.1 Update the System

Before installing any packages, it's a good idea to update your package list:

```bash
sudo apt-get update
```

### 1.2 Install RabbitMQ
```bash
sudo apt-get install rabbitmq-server -y
```

### 1.3 Enable and start RabbitMQ server
```bash
sudo systemctl enable rabbitmq-server
sudo systemctl start rabbitmq-server
```

### 1.4 Verify RabbitMQ status
```bash
sudo systemctl status rabbitmq-server
```

## Install Celery

