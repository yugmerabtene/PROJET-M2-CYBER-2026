"""DevinciWatch — simulateur d'attaquant contrôlé (serveur-attacker).

Ce script génère des scénarios de test reproduisibles et non destructeurs
pour déclencher la détection côté serveur-endpoint et produire des alertes
dans le SOC. Il ne cible que le réseau Docker de lab.

Scénarios disponibles :
1. port_scan   — tentatives de connexion TCP sur des ports courants
2. brute_force — connexions répétées sur le port 22 (SSH simulé)
3. burst       — rafale d'événements pour tester la corrélation
"""

from __future__ import annotations

import os
import socket
import time

TARGET_HOST = os.getenv("TARGET_HOST", "serveur-endpoint")
ATTACK_INTERVAL = int(os.getenv("ATTACK_INTERVAL", "30"))

SCAN_PORTS = [22, 80, 443, 3306, 5432, 8080, 8443, 9200, 27017]


def tcp_connect(host: str, port: int, timeout: float = 1.0) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except (ConnectionRefusedError, TimeoutError, OSError):
        return False


def scenario_port_scan(host: str) -> None:
    print(f"[attacker] port_scan → {host}")
    for port in SCAN_PORTS:
        result = tcp_connect(host, port)
        print(f"[attacker]   port {port:5d} {'OPEN' if result else 'closed'}")
        time.sleep(0.2)


def scenario_brute_force(host: str, attempts: int = 5) -> None:
    print(f"[attacker] brute_force SSH → {host}:22 ({attempts} tentatives)")
    for i in range(attempts):
        tcp_connect(host, 22, timeout=0.5)
        print(f"[attacker]   tentative {i + 1}/{attempts}")
        time.sleep(0.5)


def scenario_burst(host: str, count: int = 10) -> None:
    print(f"[attacker] burst → {host} ({count} connexions rapides port 80)")
    for i in range(count):
        tcp_connect(host, 80, timeout=0.3)
        time.sleep(0.1)


def run_loop() -> None:
    print(f"[attacker] démarré — cible={TARGET_HOST} intervalle={ATTACK_INTERVAL}s")
    time.sleep(15)  # laisser le SOC et l'endpoint démarrer

    while True:
        print(f"\n[attacker] === nouveau cycle de scénarios ===")
        scenario_port_scan(TARGET_HOST)
        time.sleep(5)
        scenario_brute_force(TARGET_HOST)
        time.sleep(5)
        scenario_burst(TARGET_HOST)
        print(f"[attacker] cycle terminé — pause {ATTACK_INTERVAL}s")
        time.sleep(ATTACK_INTERVAL)


if __name__ == "__main__":
    run_loop()
