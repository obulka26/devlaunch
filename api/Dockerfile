# Base image
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Copy your project files
COPY . .

# Install dependencies
RUN pip install --no-cache-dir \
    flask \
    boto3 \
    pyyaml \
    gunicorn

# Expose port 5000
EXPOSE 5000

# Production run command using gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "main:app"]

