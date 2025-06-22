FROM ubuntu:24.04

ENV NODE_VERSION=24.0.1 \
    GO_VERSION=1.24.4

# Install system dependencies
RUN apt-get update && apt-get upgrade -y && apt-get install -y \
    fish \
    xdg-utils \
    unzip \
    less \
    lsof \
    curl \
    sudo \
    gpg \
    git \
    xz-utils \
    build-essential \
    ripgrep \
    python-is-python3 \
    python3-pip \
    lsb-release \
    wget

# Add user and set up sudo
RUN useradd -m -s /usr/bin/fish user \
    && echo "user ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/user \
    && chmod 0440 /etc/sudoers.d/user


# Install NodeJS
RUN case $(uname -m) in \
    x86_64) ARCH=x64;; \
    aarch64) ARCH=arm64;; \
    *) echo "Unsupported architecture"; exit 1;; \
    esac && \
    curl -fsSL https://nodejs.org/dist/v${NODE_VERSION}/node-v${NODE_VERSION}-linux-${ARCH}.tar.xz | tar -xJf - -C /usr/local --strip-components=1

# Install Go
RUN case $(uname -m) in \
    x86_64) ARCH=amd64;; \
    aarch64) ARCH=arm64;; \
    *) echo "Unsupported architecture"; exit 1;; \
    esac && \
    curl -fsSL "https://go.dev/dl/go${GO_VERSION}.linux-${ARCH}.tar.gz" | tar -C /usr/local -xzf - && \
    echo 'export PATH=$PATH:/usr/local/go/bin' >> /etc/profile

# Switch to user
USER user

# Install the GH CLI
RUN (type -p wget >/dev/null || (sudo apt update && sudo apt-get install wget -y)) \
	&& sudo mkdir -p -m 755 /etc/apt/keyrings \
        && out=$(mktemp) && wget -nv -O$out https://cli.github.com/packages/githubcli-archive-keyring.gpg \
        && cat $out | sudo tee /etc/apt/keyrings/githubcli-archive-keyring.gpg > /dev/null \
	&& sudo chmod go+r /etc/apt/keyrings/githubcli-archive-keyring.gpg \
	&& sudo mkdir -p -m 755 /etc/apt/sources.list.d \
	&& echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null \
	&& sudo apt update \
	&& sudo apt install gh -y

# Install fr
RUN cd /home/user && \
    ARCH=$(uname -m) && \
    if [ "$ARCH" = "aarch64" ]; then \
        curl -L "https://github.com/joshuaharry/fr/releases/download/v${FR_VERSION}/fr-v${FR_VERSION}-aarch64-unknown-linux-gnu" -o "fr"; \
    else \
        curl -L "https://github.com/joshuaharry/fr/releases/download/v${FR_VERSION}/fr-v${FR_VERSION}-x86_64-unknown-linux-gnu" -o "fr"; \
    fi && \
    chmod +x fr && \
    sudo mv fr /usr/local/bin/fr

# Install par, a parallel script runner
RUN cd /home/user && \
    ARCH=$(uname -m) && \
    if [ "$ARCH" = "aarch64" ]; then \
        curl -L "https://github.com/joshuaharry/par/releases/download/v${PAR_VERSION}/par-v${PAR_VERSION}-aarch64-unknown-linux-gnu" -o "par"; \
    else \
        curl -L "https://github.com/joshuaharry/par/releases/download/v${PAR_VERSION}/par-v${PAR_VERSION}-x86_64-unknown-linux-gnu" -o "par"; \
    fi && \
    chmod +x par && \
    sudo mv par /usr/local/bin/par