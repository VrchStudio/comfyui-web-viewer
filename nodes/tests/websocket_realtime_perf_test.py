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


def _validate_channel(value, name):
    channel = int(value)
    if channel < 1 or channel > 8:
        raise ValueError(f"{name} must be between 1 and 8, got: {channel}")
    return channel


def _parse_client_cases(raw_value, default_active_clients):
    if not raw_value:
        return [max(1, int(default_active_clients))]

    tokens = []
    for token in raw_value.replace(" ", ",").split(","):
        token = token.strip()
        if token:
            tokens.append(token)

    if not tokens:
        return [max(1, int(default_active_clients))]

    cases = []
    seen = set()
    for token in tokens:
        value = int(token)
        if value <= 0:
            raise ValueError(f"active client count must be > 0, got: {value}")
        if value not in seen:
            seen.add(value)
            cases.append(value)
    return cases


async def _run_stream_case(
    sender,
    host,
    port,
    path,
    source_channel,
    target_channel,
    fps,
    duration_s,
    payload_kb_min,
    payload_kb_max,
    active_clients,
    stalled_clients,
):
    target_uri = f"ws://{host}:{port}{path}?channel={target_channel}"
    source_uri = f"ws://{host}:{port}{path}?channel={source_channel}"
    stop_recv = False
    stop_bridge = False
    call_latency_ms = []
    sent_at = {}
    seq = 0

    async with (
        websockets.connect(target_uri, max_size=None) as ws_viewer_primary,
        websockets.connect(source_uri, max_size=None) as ws_producer,
        websockets.connect(source_uri, max_size=None) as ws_bridge,
    ):
        active = [ws_viewer_primary]
        for _ in range(max(0, int(active_clients) - 1)):
            extra = await websockets.connect(target_uri, max_size=None)
            active.append(extra)

        slow_clients = []
        for _ in range(max(0, int(stalled_clients))):
            slow_client = await websockets.connect(target_uri, max_size=None, max_queue=1)
            slow_clients.append(slow_client)

        await asyncio.sleep(0.2)

        received_per_client = [[] for _ in range(len(active))]

        async def recv_loop(client_index, client_ws):
            while not stop_recv:
                try:
                    message = await asyncio.wait_for(client_ws.recv(), timeout=0.5)
                except asyncio.TimeoutError:
                    continue
                except Exception:
                    break

                if isinstance(message, (bytes, bytearray)) and len(message) >= 8:
                    frame_seq = struct.unpack(">I", message[:4])[0]
                    received_per_client[client_index].append((frame_seq, time.perf_counter()))

        async def bridge_loop():
            while not stop_bridge:
                try:
                    message = await asyncio.wait_for(ws_bridge.recv(), timeout=0.5)
                except asyncio.TimeoutError:
                    continue
                except Exception:
                    break

                if isinstance(message, (bytes, bytearray)) and len(message) >= 8:
                    t0 = time.perf_counter()
                    sender.send_to_channel(path, target_channel, message)
                    t1 = time.perf_counter()
                    call_latency_ms.append((t1 - t0) * 1000.0)

        recv_tasks = [asyncio.create_task(recv_loop(i, client_ws)) for i, client_ws in enumerate(active)]
        bridge_task = asyncio.create_task(bridge_loop())

        interval = 1.0 / max(fps, 0.1)
        start = time.perf_counter()
        next_tick = start
        payload_min = max(8, int(payload_kb_min * 1024))
        payload_max = max(payload_min, int(payload_kb_max * 1024))
        payload_span = max(1, payload_max - payload_min + 1)
        while time.perf_counter() - start < duration_s:
            now = time.perf_counter()
            if now < next_tick:
                await asyncio.sleep(next_tick - now)

            payload_size = payload_min + (seq % payload_span)
            payload = struct.pack(">II", seq, 0) + (b"\x00" * (payload_size - 8))
            t0 = time.perf_counter()
            await ws_producer.send(payload)
            sent_at[seq] = t0
            seq += 1
            next_tick += interval

        await asyncio.sleep(1.5)
        stop_recv = True
        stop_bridge = True
        if recv_tasks:
            await asyncio.gather(*recv_tasks, return_exceptions=True)
        await asyncio.gather(bridge_task, return_exceptions=True)

        for slow_client in slow_clients:
            try:
                await slow_client.close()
            except Exception:
                pass

        for extra_client in active[1:]:
            try:
                await extra_client.close()
            except Exception:
                pass

    sent_total = seq

    def build_client_stats(received):
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
            "end_to_end_latency": _summarize(e2e_latency_ms),
        }

    client_stats = [build_client_stats(received) for received in received_per_client]
    primary = client_stats[0] if client_stats else {
        "sent_frames": sent_total,
        "received_unique_frames": 0,
        "delivery_ratio": 0.0,
        "latest_received_seq": None,
        "freshness_lag_frames": sent_total,
        "end_to_end_latency": _summarize([]),
    }

    delivery_ratios = [item["delivery_ratio"] for item in client_stats] if client_stats else []
    freshness_lags = [item["freshness_lag_frames"] for item in client_stats] if client_stats else []
    p95_values = [item["end_to_end_latency"]["p95_ms"] for item in client_stats if item["end_to_end_latency"]["p95_ms"] is not None]

    return {
        "source_channel": source_channel,
        "target_channel": target_channel,
        "active_clients": len(active),
        "stalled_clients": len(slow_clients),
        "sent_frames": primary["sent_frames"],
        "received_unique_frames": primary["received_unique_frames"],
        "delivery_ratio": primary["delivery_ratio"],
        "latest_received_seq": primary["latest_received_seq"],
        "freshness_lag_frames": primary["freshness_lag_frames"],
        "send_call_latency": _summarize(call_latency_ms),
        "end_to_end_latency": primary["end_to_end_latency"],
        "multi_client_summary": {
            "clients": len(client_stats),
            "min_delivery_ratio": round(min(delivery_ratios), 4) if delivery_ratios else None,
            "avg_delivery_ratio": round(sum(delivery_ratios) / len(delivery_ratios), 4) if delivery_ratios else None,
            "max_freshness_lag_frames": max(freshness_lags) if freshness_lags else None,
            "max_end_to_end_p95_ms": max(p95_values) if p95_values else None,
        },
        "clients_detail": client_stats,
    }


async def _run(args):
    source_channel = _validate_channel(args.source_channel, "source_channel")
    target_channel = _validate_channel(args.target_channel, "target_channel")
    if source_channel == target_channel:
        raise ValueError("source_channel and target_channel must be different")

    payload_kb_min = int(args.payload_kb_min)
    payload_kb_max = int(args.payload_kb_max)
    if payload_kb_min <= 0 or payload_kb_max <= 0:
        raise ValueError("payload_kb_min and payload_kb_max must be > 0")
    if payload_kb_max < payload_kb_min:
        payload_kb_min, payload_kb_max = payload_kb_max, payload_kb_min

    if args.payload_kb is not None:
        payload_kb_min = int(args.payload_kb)
        payload_kb_max = int(args.payload_kb)

    client_cases = _parse_client_cases(args.client_cases, args.active_clients)

    output = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "config": {
            "host": args.host,
            "path": args.path,
            "source_channel": source_channel,
            "target_channel": target_channel,
            "fps": args.fps,
            "duration_s": args.duration_s,
            "payload_kb_min": payload_kb_min,
            "payload_kb_max": payload_kb_max,
            "active_clients": args.active_clients,
            "client_cases": client_cases,
            "stalled_clients": args.stalled_clients,
        },
    }

    case_results = []
    for active_clients in client_cases:
        with _server_lock:
            _port_servers.clear()

        direct_server = SimpleWebSocketServer(args.host, args.direct_port, debug=False)
        direct_server.register_path(args.path)
        await asyncio.sleep(1.0)
        direct_mode = await _run_stream_case(
            direct_server,
            args.host,
            args.direct_port,
            args.path,
            source_channel,
            target_channel,
            args.fps,
            args.duration_s,
            payload_kb_min,
            payload_kb_max,
            active_clients,
            args.stalled_clients,
        )
        direct_server.stop()
        await asyncio.sleep(0.4)

        origin = SimpleWebSocketServer(args.host, args.proxy_port, debug=False)
        origin.register_path(args.path)
        await asyncio.sleep(1.0)
        proxy_sender = get_global_server(args.host, args.proxy_port, args.path, debug=False)
        proxy_mode = await _run_stream_case(
            proxy_sender,
            args.host,
            args.proxy_port,
            args.path,
            source_channel,
            target_channel,
            args.fps,
            args.duration_s,
            payload_kb_min,
            payload_kb_max,
            active_clients,
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

        case_results.append(
            {
                "active_clients": active_clients,
                "direct_mode": direct_mode,
                "proxy_mode": proxy_mode,
            }
        )

    output["cases"] = case_results
    if case_results:
        output["direct_mode"] = case_results[0]["direct_mode"]
        output["proxy_mode"] = case_results[0]["proxy_mode"]

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
    parser.add_argument("--source-channel", type=int, default=2)
    parser.add_argument("--target-channel", type=int, default=1)
    parser.add_argument("--fps", type=float, default=15.0)
    parser.add_argument("--duration-s", type=float, default=10.0)
    parser.add_argument("--payload-kb-min", type=int, default=45)
    parser.add_argument("--payload-kb-max", type=int, default=60)
    parser.add_argument("--payload-kb", type=int, default=None, help="Override min/max with a fixed payload KB")
    parser.add_argument("--active-clients", type=int, default=2)
    parser.add_argument("--client-cases", default=None, help="Comma-separated active client counts, e.g. 1,2,5")
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
