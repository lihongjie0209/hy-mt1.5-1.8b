# Hy-MT1.5-1.8B Docker

[![Docker Hub](https://img.shields.io/docker/pulls/lihongjie0209/hy-mt1.5-1.8b)](https://hub.docker.com/r/lihongjie0209/hy-mt1.5-1.8b)

Dockerized [Hy-MT1.5-1.8B-1.25bit-GGUF](https://huggingface.co/AngelSlim/Hy-MT1.5-1.8B-1.25bit-GGUF) — a 440 MB, 1.25-bit quantized multilingual translation model supporting 33 languages.

Served via **llama-server** (OpenAI-compatible REST API).

> ⚠️ This image requires the [STQ kernel (PR #22836)](https://github.com/ggml-org/llama.cpp/pull/22836) — the official llama.cpp release does **not** work with this model.

---

## 🚀 Quick Start

### CPU Mode (default)

```bash
docker run -d \
  --name hy-mt \
  -p 8080:8080 \
  lihongjie0209/hy-mt1.5-1.8b:latest
```

### GPU Mode (NVIDIA CUDA)

Requirements: NVIDIA GPU + [nvidia-container-toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html)

```bash
docker run -d \
  --name hy-mt-gpu \
  -p 8080:8080 \
  --gpus all \
  lihongjie0209/hy-mt1.5-1.8b:cuda
```

---

## 🐳 Docker Images

| Tag | Mode | Base | Size |
|-----|------|------|------|
| `latest` / `cpu` | CPU only | `ubuntu:24.04` | ~1.5 GB |
| `cuda` | NVIDIA GPU | `nvidia/cuda:12.6.0` | ~3 GB |

---

## 📦 Docker Compose

### CPU

```yaml
services:
  hy-mt:
    image: lihongjie0209/hy-mt1.5-1.8b:latest
    ports:
      - "8080:8080"
    restart: unless-stopped
```

### GPU

```yaml
services:
  hy-mt:
    image: lihongjie0209/hy-mt1.5-1.8b:cuda
    ports:
      - "8080:8080"
    restart: unless-stopped
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]
```

---

## 🔨 Build from Source

### CPU

```bash
git clone https://github.com/lihongjie0209/hy-mt1.5-1.8b.git
cd hy-mt1.5-1.8b
docker build -t hy-mt:cpu .
```

### GPU

```bash
docker build -f Dockerfile.gpu -t hy-mt:cuda .
```

### With HuggingFace Token (if rate-limited)

```bash
docker build --build-arg HF_TOKEN=hf_xxx -t hy-mt:cpu .
```

---

## 🌐 API Usage

Once running, the server exposes an **OpenAI-compatible API** at `http://localhost:8080`.

### Health Check

```bash
curl http://localhost:8080/health
# {"status":"ok"}
```

### Translation

```bash
curl http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{
      "role": "user",
      "content": "Translate the following segment into Chinese, without additional explanation：Hello world"
    }],
    "max_tokens": 128
  }'
```

### Prompt Format

The model follows a simple instruction format:

```
Translate the following segment into {language}, without additional explanation：{source text}
```

**Supported target languages (examples):**

| Language | Keyword |
|----------|---------|
| 中文 | `Chinese` |
| English | `English` |
| 日本語 | `Japanese` |
| Français | `French` |
| Deutsch | `German` |
| Español | `Spanish` |
| 한국어 | `Korean` |
| Русский | `Russian` |
| العربية | `Arabic` |

The model natively supports **33 languages and 1,056 translation directions**.

---

## ⚡ Performance

Benchmark results on CPU (Docker Desktop, Windows, measured with `bench.py`):

| Concurrency | QPS | Token Throughput | P50 Latency | P99 Latency |
|-------------|-----|-----------------|-------------|-------------|
| 1 | 0.27 req/s | 1.9 tok/s | 3553 ms | 5055 ms |
| 2 | 0.44 req/s | 3.0 tok/s | 4274 ms | 7432 ms |
| 4 | 0.53 req/s | 3.7 tok/s | 7006 ms | 10457 ms |

> GPU mode is significantly faster. With CUDA, expect 10–50× throughput improvement.

---

## 🔧 Configuration

| Parameter | Default | Description |
|-----------|---------|-------------|
| `--ctx-size` | 2048 | Context window size |
| `-ngl` | `0` (CPU) / `99` (GPU) | GPU layers to offload |
| `--port` | 8080 | Server port |
| `--host` | 0.0.0.0 | Bind address |

Override at runtime:

```bash
docker run -d -p 8080:8080 lihongjie0209/hy-mt1.5-1.8b:latest \
  llama-server \
    --model /models/Hy-MT1.5-1.8B-1.25bit.gguf \
    --host 0.0.0.0 --port 8080 \
    -ngl 0 --ctx-size 4096
```

---

## 📄 License

Model weights are subject to the [AngelSlim License](https://huggingface.co/AngelSlim/Hy-MT1.5-1.8B-1.25bit-GGUF).
Docker configuration in this repo is MIT licensed.

---

## 🔗 References

- [Hy-MT1.5-1.8B-1.25bit-GGUF on HuggingFace](https://huggingface.co/AngelSlim/Hy-MT1.5-1.8B-1.25bit-GGUF)
- [HY-MT1.5 Technical Report](https://arxiv.org/abs/2512.24092)
- [Sherry: 1.25-bit Quantization (ACL 2026)](https://arxiv.org/abs/2601.07892)
- [llama.cpp STQ kernel PR #22836](https://github.com/ggml-org/llama.cpp/pull/22836)
