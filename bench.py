"""
Hy-MT1.5-1.8B llama-server 压测脚本
- 并发多个翻译请求
- 统计 QPS、延迟（P50/P90/P99）、成功率、token 吞吐量
"""

import asyncio
import time
import statistics
import json
import sys
from dataclasses import dataclass, field

import httpx

BASE_URL = "http://localhost:8080"
ENDPOINT = f"{BASE_URL}/v1/chat/completions"

SENTENCES = [
    "Hello, how are you?",
    "The weather is nice today.",
    "I would like to order a coffee, please.",
    "Where is the nearest train station?",
    "Can you help me with this problem?",
    "The quick brown fox jumps over the lazy dog.",
    "Technology is changing the world rapidly.",
    "Please translate this text into Chinese.",
    "I am learning a new programming language.",
    "The meeting is scheduled for tomorrow morning.",
]


@dataclass
class Result:
    success: bool
    latency_ms: float
    tokens_out: int = 0
    error: str = ""


async def single_request(client: httpx.AsyncClient, sentence: str) -> Result:
    payload = {
        "messages": [{"role": "user", "content": f"Translate to Chinese: {sentence}"}],
        "max_tokens": 64,
        "temperature": 0,
    }
    t0 = time.perf_counter()
    try:
        resp = await client.post(ENDPOINT, json=payload, timeout=60)
        latency_ms = (time.perf_counter() - t0) * 1000
        if resp.status_code == 200:
            data = resp.json()
            tokens = data.get("usage", {}).get("completion_tokens", 0)
            return Result(success=True, latency_ms=latency_ms, tokens_out=tokens)
        else:
            return Result(success=False, latency_ms=latency_ms, error=f"HTTP {resp.status_code}")
    except Exception as e:
        latency_ms = (time.perf_counter() - t0) * 1000
        return Result(success=False, latency_ms=latency_ms, error=str(e))


async def run_bench(concurrency: int, total_requests: int):
    print(f"\n{'='*60}")
    print(f"  并发数: {concurrency}   总请求数: {total_requests}")
    print(f"{'='*60}")

    semaphore = asyncio.Semaphore(concurrency)
    results: list[Result] = []

    async def bounded(i: int):
        sentence = SENTENCES[i % len(SENTENCES)]
        async with semaphore:
            r = await single_request(client, sentence)
            results.append(r)
            status = "✓" if r.success else "✗"
            print(f"  [{i+1:>3}/{total_requests}] {status}  {r.latency_ms:7.0f} ms  "
                  f"{'tokens=' + str(r.tokens_out) if r.success else r.error}")

    async with httpx.AsyncClient() as client:
        wall_start = time.perf_counter()
        await asyncio.gather(*[bounded(i) for i in range(total_requests)])
        wall_elapsed = time.perf_counter() - wall_start

    # ── Stats ──────────────────────────────────────────────
    ok = [r for r in results if r.success]
    fail = [r for r in results if not r.success]
    latencies = [r.latency_ms for r in ok]
    total_tokens = sum(r.tokens_out for r in ok)

    print(f"\n{'─'*60}")
    print(f"  总耗时       : {wall_elapsed:.2f} s")
    print(f"  成功 / 失败  : {len(ok)} / {len(fail)}")
    print(f"  QPS          : {len(ok)/wall_elapsed:.2f} req/s")
    print(f"  Token 吞吐   : {total_tokens/wall_elapsed:.1f} tokens/s")
    if latencies:
        latencies_sorted = sorted(latencies)
        print(f"  延迟 P50     : {statistics.median(latencies_sorted):.0f} ms")
        print(f"  延迟 P90     : {latencies_sorted[int(len(latencies_sorted)*0.9)]:.0f} ms")
        print(f"  延迟 P99     : {latencies_sorted[int(len(latencies_sorted)*0.99)]:.0f} ms")
        print(f"  延迟 最小/最大: {min(latencies):.0f} / {max(latencies):.0f} ms")
    print(f"{'─'*60}\n")


async def main():
    # 预热
    print("🔥 预热中...")
    async with httpx.AsyncClient() as client:
        await single_request(client, "Hello")
    print("✅ 预热完成\n")

    # 压测矩阵：(并发, 请求数)
    scenarios = [
        (1, 10),
        (2, 20),
        (4, 20),
    ]
    for concurrency, total in scenarios:
        await run_bench(concurrency, total)


if __name__ == "__main__":
    asyncio.run(main())
