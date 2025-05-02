FROM python:3.10-slim-bullseye


# System deps
RUN apt-get update && apt-get install -y \
    gcc g++ build-essential curl \
    unixodbc-dev gnupg2 apt-transport-https \
    && rm -rf /var/lib/apt/lists/*

# Add Microsoft GPG key (recommended way)
RUN curl -sSL https://packages.microsoft.com/keys/microsoft.asc -o microsoft.asc \
    && gpg --dearmor microsoft.asc \
    && mv microsoft.asc.gpg /usr/share/keyrings/microsoft.gpg \
    && rm microsoft.asc

# Add Microsoft repository for Debian 11 (Bullseye)
RUN echo "deb [arch=amd64 signed-by=/usr/share/keyrings/microsoft.gpg] https://packages.microsoft.com/debian/11/prod bullseye main" \
    > /etc/apt/sources.list.d/mssql-release.list

# Install MS ODBC driver
RUN apt-get update \
    && ACCEPT_EULA=Y apt-get install -y msodbcsql18 \
    && rm -rf /var/lib/apt/lists/*

# Application workdir
WORKDIR /app

# Install Python dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
