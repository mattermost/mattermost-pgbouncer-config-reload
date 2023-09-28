# Use python:3-alpine as the base image
FROM python:3-alpine as base

# Install necessary system dependencies
RUN apk update && apk add postgresql-dev gcc python3-dev musl-dev postgresql-client libpq

# Set working directory
WORKDIR /opt

# Copy the current directory contents into the container at /opt
COPY . /opt

# Upgrade pip and install Python dependencies from requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Set necessary volumes
VOLUME ["/etc/pgbouncer/", "/etc/userlist/"]

# Switch to a non-root user
USER nobody

# Set the entry point for the container
ENTRYPOINT ["pgbouncer-config-reload", "-vv"]
