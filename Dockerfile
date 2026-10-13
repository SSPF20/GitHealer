# 1. Use the official lightweight Python 3.12 slim base image
FROM python:3.12-slim

# 2. Set the working directory inside the container
WORKDIR /app

# 3. Copy requirements and install pytest and dependencies inside the container
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# 4. Default command when container runs
CMD ["pytest"]