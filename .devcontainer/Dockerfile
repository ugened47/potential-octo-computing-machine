# Development container with Python and Node.js
FROM mcr.microsoft.com/devcontainers/base:ubuntu

# Install system dependencies
RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
    && apt-get -y install --no-install-recommends \
    # Build tools
    build-essential \
    cmake \
    pkg-config \
    # Python dependencies
    python3.11 \
    python3.11-dev \
    python3-pip \
    python3.11-venv \
    # Video/Audio processing
    ffmpeg \
    libsndfile1 \
    libsndfile1-dev \
    libgomp1 \
    libavcodec-dev \
    libavformat-dev \
    libavutil-dev \
    libswscale-dev \
    # Image processing
    libopencv-dev \
    # Audio libraries
    libasound2-dev \
    libportaudio2 \
    portaudio19-dev \
    # Database clients
    postgresql-client \
    redis-tools \
    # Network tools
    curl \
    wget \
    netcat \
    # Git
    git \
    git-lfs \
    # Other utilities
    vim \
    nano \
    htop \
    jq \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Set Python 3.11 as default
RUN update-alternatives --install /usr/bin/python python /usr/bin/python3.11 1 \
    && update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1

# Install Node.js 20 (LTS)
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Install pnpm and yarn
RUN npm install -g pnpm yarn

# Install Python tools globally
RUN pip3 install --no-cache-dir \
    ruff \
    mypy \
    black \
    pytest \
    pytest-asyncio \
    pytest-cov \
    ipython \
    alembic

# Create workspace directory
RUN mkdir -p /workspace

# Setup non-root user
ARG USERNAME=vscode
ARG USER_UID=1000
ARG USER_GID=$USER_UID

RUN groupadd --gid $USER_GID $USERNAME \
    && useradd --uid $USER_UID --gid $USER_GID -m $USERNAME \
    && apt-get update \
    && apt-get install -y sudo \
    && echo $USERNAME ALL=\(root\) NOPASSWD:ALL > /etc/sudoers.d/$USERNAME \
    && chmod 0440 /etc/sudoers.d/$USERNAME \
    && rm -rf /var/lib/apt/lists/*

# Set ownership
RUN chown -R $USERNAME:$USERNAME /workspace

# Switch to non-root user
USER $USERNAME

# Set working directory
WORKDIR /workspace

# Keep container running
CMD ["sleep", "infinity"]
