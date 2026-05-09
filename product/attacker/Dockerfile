FROM python:3.12-slim

WORKDIR /app

# Install dependencies and build tools
RUN apt-get update && apt-get install -y \
    build-essential \
    pkg-config \
    libssl-dev \
    nmap \
    curl \
    wget \
    netcat-openbsd \
    iputils-ping \
    dnsutils \
    tcpdump \
    slowhttptest \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install ffuf (Go tool)
RUN wget https://github.com/ffuf/ffuf/releases/download/v2.1.0/ffuf_2.1.0_linux_amd64.tar.gz && \
    tar -xzf ffuf_2.1.0_linux_amd64.tar.gz -C /usr/local/bin && \
    rm ffuf_*.tar.gz

# Install hydra from source
RUN git clone https://github.com/vanhauser-thc/thc-hydra.git /tmp/hydra && \
    cd /tmp/hydra && \
    ./configure && \
    make && \
    make install && \
    rm -rf /tmp/hydra

# Install nikto from source
RUN git clone https://github.com/sullo/nikto.git /opt/nikto && \
    ln -s /opt/nikto/program/nikto.pl /usr/local/bin/nikto && \
    apt-get update && apt-get install -y libwww-perl && \
    rm -rf /var/lib/apt/lists/*

# Install Go for additional tools
RUN wget https://go.dev/dl/go1.22.3.linux-amd64.tar.gz && \
    tar -C /usr/local -xzf go1.22.3.linux-amd64.tar.gz && \
    rm go1.22.3.linux-amd64.tar.gz

ENV PATH=$PATH:/usr/local/go/bin

# Install httpx and other Go tools
RUN go install -v github.com/projectdiscovery/httpx/cmd/httpx@latest && \
    cp /root/go/bin/httpx /usr/local/bin/

# Copy Python scripts
COPY . .

# Install Python dependencies if any
RUN pip install --no-cache-dir requests redis

CMD ["python", "scenario.py"]
