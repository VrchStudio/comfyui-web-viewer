#!/usr/bin/env python3
"""WebSocket server performance benchmark.

This script benchmarks both direct server mode and proxy mode,
and can compare current results with a baseline JSON.
"""

import argparse
import asyncio
import json
import statistics
import sys
import time
from pathlib import Path

import websockets

sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.websocket_server import SimpleWebSocketServer, get_global_server, _port_servers, _server_lock  # noqa: E402


async def _connect_clients(host, port, path, channel, count):
    uri = f"ws://{host}:{port}{path}?channel={channel}"
    clients = []
    for _ in range(count):
        ws = await websockets.connect(uri)
        clients.append(ws)
    await asyncio.sleep(0.2)
    return clients


def _summarize(values):
    if not values:
        return {
            "count": 0,
            "p50_ms": None,
            "p95_ms": None,
            "p99_ms": None,
            "avg_ms": None,
        }

    p50 = statistics.median(values)
    p95 = statistics.quantiles(values, n=100)[94] if len(values) >= 20 else max(values)
    p99 = statistics.quantiles(values, n=100)[98] if len(values) >= 100 else max(values)

    return {
        "count": len(values),
        "p50_ms": round(p50, 3),
        "p95_ms": round(p95, 3),
        "p99_ms": round(p99, 3),
        "avg_ms": round(statistics.mean(values), 3),
    }


async def _bench_sender(sender, path, channel, recv_clients, messages):
    call_latency_ms = []
    e2e_latency_ms = []
    ok = 0

    for idx in range(messages):
        payload = f"bench-{idx}"
        recv_tasks = [
            asyncio.create_task(asyncio.wait_for(ws.recv(), timeout=3.0))
            for ws in recv_clients
        ]

        t0 = time.perf_counter()
        sender.send_to_channel(path, channel, payload)
        t1 = time.perf_counter()
        recv_results = await asyncio.gather(*recv_tasks, return_exceptions=True)
        t2 = time.perf_counter()

        if all((not isinstance(msg, Exception) and msg == payload) for msg in recv_results):
            ok += 1
            call_latency_ms.append((t1 - t0) * 1000.0)
            e2e_latency_ms.append((t2 - t0) * 1000.0)

    result = {
        "messages_total": messages,
        "messages_ok": ok,
        "send_call_latency": _summarize(call_latency_ms),
        "end_to_end_latency": _summarize(e2e_latency_ms),
    }

    if e2e_latency_ms:
        deliveries = len(e2e_latency_ms) * len(recv_clients)
        elapsed = sum(e2e_latency_ms) / 1000.0
        result["delivery_per_sec"] = round(deliveries / elapsed, 2)
    else:
        result["delivery_per_sec"] = 0.0

    return result


def _delta_pct(before, after):
    if before in (None, 0) or after is None:
        return None
    return round(((after - before) / before) * 100.0, 2)


def _build_comparison(baseline, current):
    if not baseline:
        return None

    comparison = {}
    for mode in ("direct_mode", "proxy_mode"):
        b_mode = baseline.get(mode, {})
        c_mode = current.get(mode, {})

        b_call = b_mode.get("send_call_latency", {})
        c_call = c_mode.get("send_call_latency", {})
        b_e2e = b_mode.get("end_to_end_latency", {})
        c_e2e = c_mode.get("end_to_end_latency", {})

        comparison[mode] = {
            "send_call_p95_delta_pct": _delta_pct(b_call.get("p95_ms"), c_call.get("p95_ms")),
            "e2e_p95_delta_pct": _delta_pct(b_e2e.get("p95_ms"), c_e2e.get("p95_ms")),
            "delivery_per_sec_delta_pct": _delta_pct(
                b_mode.get("delivery_per_sec"),
                c_mode.get("delivery_per_sec"),
            ),
        }

    return comparison


def _write_markdown_report(path, baseline, current, comparison):
    lines = []
    lines.append("# WebSocket Server Performance Report")
    lines.append("")
    lines.append(f"- Timestamp: {current['timestamp']}")
    lines.append(
        f"- Config: clients={current['config']['clients']}, messages={current['config']['messages']}, "
        f"path={current['config']['path']}, channel={current['config']['channel']}"
    )
    lines.append("")

    def add_mode(title, mode_key):
        mode = current[mode_key]
        lines.append(f"## {title}")
        lines.append("")
        lines.append(f"- Messages OK: {mode['messages_ok']}/{mode['messages_total']}")
        lines.append(f"- Send call p95: {mode['send_call_latency']['p95_ms']} ms")
        lines.append(f"- End-to-end p95: {mode['end_to_end_latency']['p95_ms']} ms")
        lines.append(f"- Delivery throughput: {mode['delivery_per_sec']} msg-deliveries/s")
        lines.append("")

        if baseline and comparison:
            b_mode = baseline.get(mode_key, {})
            cmp = comparison.get(mode_key, {})
            lines.append("### Delta vs Baseline")
            lines.append("")
            lines.append(
                f"- Send call p95 delta: {cmp.get('send_call_p95_delta_pct')}% "
                f"(before={b_mode.get('send_call_latency', {}).get('p95_ms')} ms)"
            )
            lines.append(
                f"- End-to-end p95 delta: {cmp.get('e2e_p95_delta_pct')}% "
                f"(before={b_mode.get('end_to_end_latency', {}).get('p95_ms')} ms)"
            )
            lines.append(
                f"- Delivery throughput delta: {cmp.get('delivery_per_sec_delta_pct')}% "
                f"(before={b_mode.get('delivery_per_sec')} msg-deliveries/s)"
            )
            lines.append("")

    add_mode("Direct Mode", "direct_mode")
    add_mode("Proxy Mode", "proxy_mode")

    path.write_text("\n".join(lines), encoding="utf-8")


async def run_benchmark(args):
    host = args.host
    with _server_lock:
        _port_servers.clear()

    result = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "config": {
            "host": host,
            "clients": args.clients,
            "messages": args.messages,
            "path": args.path,
            "channel": args.channel,
        },
    }

    # Direct mode benchmark.
    direct_server = SimpleWebSocketServer(host, args.direct_port, debug=False)
    direct_server.register_path(args.path)
    time.sleep(1.0)

    direct_clients = await _connect_clients(host, args.direct_port, args.path, args.channel, args.clients)
    result["direct_mode"] = await _bench_sender(
        direct_server,
        args.path,
        args.channel,
        direct_clients,
        args.messages,
    )

    for ws in direct_clients:
        await ws.close()

    direct_server.stop()
    time.sleep(0.4)

    # Proxy mode benchmark (port in use path).
    origin_server = SimpleWebSocketServer(host, args.proxy_port, debug=False)
    origin_server.register_path(args.path)
    time.sleep(1.0)

    proxy_sender = get_global_server(host, args.proxy_port, args.path, debug=False)
    proxy_clients = await _connect_clients(host, args.proxy_port, args.path, args.channel, args.clients)
    result["proxy_mode"] = await _bench_sender(
        proxy_sender,
        args.path,
        args.channel,
        proxy_clients,
        args.messages,
    )

    for ws in proxy_clients:
        await ws.close()

    try:
        proxy_sender.stop()
    except Exception:
        pass

    origin_server.stop()
    time.sleep(0.4)

    with _server_lock:
        for server in list(_port_servers.values()):
            try:
                if hasattr(server, "stop"):
                    server.stop()
            except Exception:
                pass
        _port_servers.clear()

    return result


def parse_args():
    parser = argparse.ArgumentParser(description="Benchmark websocket_server direct and proxy mode")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--path", default="/bench")
    parser.add_argument("--channel", type=int, default=1)
    parser.add_argument("--clients", type=int, default=20)
    parser.add_argument("--messages", type=int, default=80)
    parser.add_argument("--direct-port", type=int, default=9401)
    parser.add_argument("--proxy-port", type=int, default=9402)
    parser.add_argument("--output-json", type=Path, default=None)
    parser.add_argument("--baseline-json", type=Path, default=None)
    parser.add_argument("--output-report", type=Path, default=None)
    return parser.parse_args()


def main():
    args = parse_args()

    current = asyncio.run(run_benchmark(args))

    baseline = None
    if args.baseline_json and args.baseline_json.exists():
        baseline = json.loads(args.baseline_json.read_text(encoding="utf-8"))

    comparison = _build_comparison(baseline, current)
    payload = {"baseline": baseline, "current": current, "comparison": comparison}

    print(json.dumps(payload, indent=2))

    if args.output_json:
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    if args.output_report:
        args.output_report.parent.mkdir(parents=True, exist_ok=True)
        _write_markdown_report(args.output_report, baseline, current, comparison)


if __name__ == "__main__":
    main()
