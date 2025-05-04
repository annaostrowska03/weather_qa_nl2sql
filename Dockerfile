FROM python:3.10-slim-bullseye

# System dependencies
RUN apt-get update && apt-get install -y \
    gcc g++ build-essential curl gnupg2 apt-transport-https unixodbc-dev openjdk-17-jre \
    && rm -rf /var/lib/apt/lists/*

# Add Microsoft GPG key and repository for Debian 11 (Bullseye)
RUN curl -sSL https://packages.microsoft.com/keys/microsoft.asc -o microsoft.asc \
    && gpg --dearmor microsoft.asc \
    && mv microsoft.asc.gpg /usr/share/keyrings/microsoft.gpg \
    && echo "deb [arch=amd64 signed-by=/usr/share/keyrings/microsoft.gpg] https://packages.microsoft.com/debian/11/prod bullseye main" \
    > /etc/apt/sources.list.d/mssql-release.list \
    && rm microsoft.asc

# Install MS ODBC driver
RUN apt-get update \
    && ACCEPT_EULA=Y apt-get install -y msodbcsql17 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
