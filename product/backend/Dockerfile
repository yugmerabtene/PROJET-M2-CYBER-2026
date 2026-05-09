FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    pkg-config \
    libssl-dev \
    nmap \
    curl \
    wget \
    git \
    netcat-openbsd \
    iputils-ping \
    dnsutils \
    tcpdump \
    slowhttptest \
    libwww-perl \
    && rm -rf /var/lib/apt/lists/*

RUN wget https://github.com/ffuf/ffuf/releases/download/v2.1.0/ffuf_2.1.0_linux_amd64.tar.gz && \
    tar -xzf ffuf_2.1.0_linux_amd64.tar.gz -C /usr/local/bin && \
    rm ffuf_*.tar.gz

RUN git clone https://github.com/vanhauser-thc/thc-hydra.git /tmp/hydra && \
    cd /tmp/hydra && \
    ./configure && \
    make && \
    make install && \
    rm -rf /tmp/hydra

RUN git clone https://github.com/sullo/nikto.git /opt/nikto && \
    ln -s /opt/nikto/program/nikto.pl /usr/local/bin/nikto

RUN wget https://go.dev/dl/go1.22.3.linux-amd64.tar.gz && \
    tar -C /usr/local -xzf go1.22.3.linux-amd64.tar.gz && \
    rm go1.22.3.linux-amd64.tar.gz

ENV PATH=$PATH:/usr/local/go/bin

RUN go install -v github.com/projectdiscovery/httpx/cmd/httpx@latest && \
    cp /root/go/bin/httpx /usr/local/bin/

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
