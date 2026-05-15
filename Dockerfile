# ============================================================
# Stage 1: Build llama.cpp with STQ kernel (PR #22836)
# ============================================================
FROM ubuntu:24.04 AS builder

ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    git \
    cmake \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build

# Clone llama.cpp and checkout the STQ kernel PR branch
RUN git clone https://github.com/ggml-org/llama.cpp.git && \
    cd llama.cpp && \
    git fetch origin pull/22836/head:pr-22836-stq_0 && \
    git checkout pr-22836-stq_0

# Build only llama-server (CPU-only, static linking to avoid missing .so in runtime)
RUN cd llama.cpp && \
    cmake -B build \
        -DGGML_CUDA=OFF \
        -DBUILD_SHARED_LIBS=OFF \
        -DLLAMA_BUILD_TESTS=OFF \
        -DLLAMA_BUILD_EXAMPLES=OFF && \
    cmake --build build --config Release --target llama-server -j$(nproc)

# ============================================================
# Stage 2: Download the GGUF model from HuggingFace
# ============================================================
FROM python:3.12-slim AS downloader

ARG HF_TOKEN=""

RUN pip install --no-cache-dir huggingface-hub

# Download the 1.25-bit GGUF model (~440MB)
# huggingface-hub >= 0.27 ships `hf` as the new CLI (huggingface-cli is deprecated)
RUN if [ -n "$HF_TOKEN" ]; then \
        hf download \
            AngelSlim/Hy-MT1.5-1.8B-1.25bit-GGUF \
            Hy-MT1.5-1.8B-1.25bit.gguf \
            --local-dir /models \
            --token "$HF_TOKEN"; \
    else \
        hf download \
            AngelSlim/Hy-MT1.5-1.8B-1.25bit-GGUF \
            Hy-MT1.5-1.8B-1.25bit.gguf \
            --local-dir /models; \
    fi

# ============================================================
# Stage 3: Runtime image (minimal)
# ============================================================
FROM ubuntu:24.04 AS runtime

ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    libgomp1 \
    ca-certificates \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy the server binary from builder
COPY --from=builder /build/llama.cpp/build/bin/llama-server /usr/local/bin/llama-server

# Copy the model from downloader
COPY --from=downloader /models /models

EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Start llama-server with CPU-only inference
CMD ["llama-server", \
     "--model", "/models/Hy-MT1.5-1.8B-1.25bit.gguf", \
     "--host", "0.0.0.0", \
     "--port", "8080", \
     "-ngl", "0", \
     "--ctx-size", "2048"]
