#!/usr/bin/env python3
"""Realtime-focused websocket performance benchmark.

This benchmark simulates continuous large binary frame streaming (e.g. /image).
It reports sender call latency and freshness (how close receiver stays to latest frame).
"""

import argparse
import asyncio
import json
import statistics
import struct
import sys
import time
from pathlib import Path

import websockets

sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.websocket_server import SimpleWebSocketServer, get_global_server, _port_servers, _server_lock  # noqa: E402


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


def _delta_pct_lower_is_better(before, after):
    if before in (None, 0) or after is None:
        return None
    return round(((before - after) / before) * 100.0, 2)


async def _run_stream_case(
    sender,
    host,
    port,
    path,
    channel,
    fps,
    duration_s,
    payload_kb,
    stalled_clients,
):
    uri = f"ws://{host}:{port}{path}?channel={channel}"
    recv_task = None
    stop_recv = False
    call_latency_ms = []
    sent_at = {}
    received = []
    seq = 0

    payload_size = max(8, int(payload_kb * 1024))
    payload_body = b"\x00" * (payload_size - 8)

    async with websockets.connect(uri, max_size=None) as ws:
        slow_clients = []
        for _ in range(max(0, stalled_clients)):
            slow_client = await websockets.connect(uri, max_size=None, max_queue=1)
            slow_clients.append(slow_client)

        await asyncio.sleep(0.2)

        async def recv_loop():
            while not stop_recv:
                try:
                    message = await asyncio.wait_for(ws.recv(), timeout=0.5)
                except asyncio.TimeoutError:
                    continue
                except Exception:
                    break

                if isinstance(message, (bytes, bytearray)) and len(message) >= 8:
                    frame_seq = struct.unpack(">I", message[:4])[0]
                    received.append((frame_seq, time.perf_counter()))

        recv_task = asyncio.create_task(recv_loop())

        interval = 1.0 / max(fps, 0.1)
        start = time.perf_counter()
        next_tick = start
        while time.perf_counter() - start < duration_s:
            now = time.perf_counter()
            if now < next_tick:
                await asyncio.sleep(next_tick - now)
            payload = struct.pack(">II", seq, 0) + payload_body
            t0 = time.perf_counter()
            sender.send_to_channel(path, channel, payload)
            t1 = time.perf_counter()
            call_latency_ms.append((t1 - t0) * 1000.0)
            sent_at[seq] = t0
            seq += 1
            next_tick += interval

        await asyncio.sleep(1.5)
        stop_recv = True
        if recv_task is not None:
            await recv_task

        for slow_client in slow_clients:
            try:
                await slow_client.close()
            except Exception:
                pass

    sent_total = seq
    unique_received = {}
    for frame_seq, recv_time in received:
        unique_received[frame_seq] = recv_time

    received_total = len(unique_received)
    latest_received = max(unique_received.keys()) if unique_received else None
    freshness_lag_frames = sent_total if latest_received is None else max(0, (sent_total - 1) - latest_received)

    e2e_latency_ms = []
    for frame_seq, recv_time in unique_received.items():
        sent_time = sent_at.get(frame_seq)
        if sent_time is not None:
            e2e_latency_ms.append((recv_time - sent_time) * 1000.0)

    return {
        "sent_frames": sent_total,
        "received_unique_frames": received_total,
        "delivery_ratio": round((received_total / sent_total), 4) if sent_total else 0.0,
        "latest_received_seq": latest_received,
        "freshness_lag_frames": freshness_lag_frames,
        "send_call_latency": _summarize(call_latency_ms),
        "end_to_end_latency": _summarize(e2e_latency_ms),
    }


async def _run(args):
    with _server_lock:
        _port_servers.clear()

    output = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "config": {
            "host": args.host,
            "path": args.path,
            "channel": args.channel,
            "fps": args.fps,
            "duration_s": args.duration_s,
            "payload_kb": args.payload_kb,
            "stalled_clients": args.stalled_clients,
        },
    }

    direct_server = SimpleWebSocketServer(args.host, args.direct_port, debug=False)
    direct_server.register_path(args.path)
    await asyncio.sleep(1.0)
    output["direct_mode"] = await _run_stream_case(
        direct_server,
        args.host,
        args.direct_port,
        args.path,
        args.channel,
        args.fps,
        args.duration_s,
        args.payload_kb,
        args.stalled_clients,
    )
    direct_server.stop()
    await asyncio.sleep(0.4)

    origin = SimpleWebSocketServer(args.host, args.proxy_port, debug=False)
    origin.register_path(args.path)
    await asyncio.sleep(1.0)
    proxy_sender = get_global_server(args.host, args.proxy_port, args.path, debug=False)
    output["proxy_mode"] = await _run_stream_case(
        proxy_sender,
        args.host,
        args.proxy_port,
        args.path,
        args.channel,
        args.fps,
        args.duration_s,
        args.payload_kb,
        args.stalled_clients,
    )
    try:
        proxy_sender.stop()
    except Exception:
        pass
    origin.stop()
    await asyncio.sleep(0.4)

    with _server_lock:
        for server in list(_port_servers.values()):
            try:
                if hasattr(server, "stop"):
                    server.stop()
            except Exception:
                pass
        _port_servers.clear()

    return output


def _build_comparison(baseline, current):
    if not baseline:
        return None
    comp = {}
    for mode in ("direct_mode", "proxy_mode"):
        b = baseline.get(mode, {})
        c = current.get(mode, {})
        comp[mode] = {
            "send_call_p95_improve_pct": _delta_pct_lower_is_better(
                b.get("send_call_latency", {}).get("p95_ms"),
                c.get("send_call_latency", {}).get("p95_ms"),
            ),
            "e2e_p95_improve_pct": _delta_pct_lower_is_better(
                b.get("end_to_end_latency", {}).get("p95_ms"),
                c.get("end_to_end_latency", {}).get("p95_ms"),
            ),
            "freshness_lag_improve_pct": _delta_pct_lower_is_better(
                b.get("freshness_lag_frames"),
                c.get("freshness_lag_frames"),
            ),
        }
    return comp


def _parse_args():
    parser = argparse.ArgumentParser(description="Realtime websocket performance benchmark")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--path", default="/image")
    parser.add_argument("--channel", type=int, default=1)
    parser.add_argument("--fps", type=float, default=15.0)
    parser.add_argument("--duration-s", type=float, default=8.0)
    parser.add_argument("--payload-kb", type=int, default=96)
    parser.add_argument("--stalled-clients", type=int, default=0)
    parser.add_argument("--direct-port", type=int, default=9501)
    parser.add_argument("--proxy-port", type=int, default=9502)
    parser.add_argument("--baseline-json", type=Path, default=None)
    parser.add_argument("--output-json", type=Path, default=None)
    return parser.parse_args()


def main():
    args = _parse_args()
    current = asyncio.run(_run(args))

    baseline = None
    if args.baseline_json and args.baseline_json.exists():
        loaded = json.loads(args.baseline_json.read_text(encoding="utf-8"))
        if isinstance(loaded, dict) and isinstance(loaded.get("current"), dict):
            baseline = loaded["current"]
        else:
            baseline = loaded

    payload = {
        "baseline": baseline,
        "current": current,
        "comparison": _build_comparison(baseline, current),
    }
    print(json.dumps(payload, indent=2))

    if args.output_json:
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
