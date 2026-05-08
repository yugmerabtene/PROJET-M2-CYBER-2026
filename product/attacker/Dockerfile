FROM python:3.12-slim

WORKDIR /app

# Install attack tools and dependencies
RUN apt-get update && apt-get install -y \
    nmap \
    nikto \
    ffuf \
    hydra \
    curl \
    wget \
    netcat-openbsd \
    iputils-ping \
    dnsutils \
    tcpdump \
    slowhttptest \
    && rm -rf /var/lib/apt/lists/*

# Install Go for additional tools (optional)
RUN wget https://go.dev/dl/go1.22.3.linux-amd64.tar.gz && \
    tar -C /usr/local -xzf go1.22.3.linux-amd64.tar.gz && \
    rm go1.22.3.linux-amd64.tar.gz

ENV PATH=$PATH:/usr/local/go/bin

# Install additional tools with Go
RUN go install -v github.com/projectdiscovery/httpx/cmd/httpx@latest && \
    go install -v github.com/ffuf/ffuf@latest

# Copy Python scripts
COPY . .

# Install Python dependencies if any
RUN pip install --no-cache-dir requests

CMD ["python", "scenario.py"]
