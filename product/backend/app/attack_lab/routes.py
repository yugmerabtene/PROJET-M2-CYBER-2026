from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Optional
import json
import subprocess
import asyncio
import redis
import logging
from datetime import datetime, timezone

from app.core.config import settings
from app.core.deps import get_current_user, get_db
from app.auth.models import User

router = APIRouter()
logger = logging.getLogger(__name__)

# Redis connection for job queue and live logs
redis_client = redis.Redis.from_url(settings.redis_url, decode_responses=True)

# Allowlist des cibles autorisées
TARGET_ALLOWLIST = [
    "serveur-endpoint",
    "127.0.0.1",
    "localhost",
    "devinciwatch-test"
]

# Scénarios d'attaque disponibles
ATTACK_SCENARIOS = {
    "recon_nmap": {
        "name": "Reconnaissance Nmap",
        "tool": "nmap",
        "description": "Scan de ports avec nmap",
        "intensity": {"low": "-sS -p 22,80,443", "medium": "-sS -p 1-1000", "high": "-sS -p-", "stress": "-sS -p- -T5"}
    },
    "recon_httpx": {
        "name": "Reconnaissance HTTP",
        "tool": "httpx",
        "description": "Fingerprint HTTP",
        "intensity": {"low": "-u TARGET -silent", "medium": "-u TARGET -tech-detect", "high": "-u TARGET -probe-all", "stress": "-u TARGET -probe-all -threads 100"}
    },
    "web_ffuf": {
        "name": "Directory Bruteforce",
        "tool": "ffuf",
        "description": "Fuzzing de répertoires web",
        "intensity": {"low": "-u TARGET/FUZZ -w /usr/share/wordlists/dirb/small.txt", "medium": "-u TARGET/FUZZ -w /usr/share/wordlists/dirb/common.txt", "high": "-u TARGET/FUZZ -w /usr/share/wordlists/dirb/big.txt", "stress": "-u TARGET/FUZZ -w /usr/share/wordlists/dirb/big.txt -t 100"}
    },
    "bruteforce_hydra": {
        "name": "Brute Force Hydra",
        "tool": "hydra",
        "description": "Attaque brute force contrôlée",
        "intensity": {"low": "-l admin -P /usr/share/wordlists/rockyou.txt.gz TARGET http-post-form", "medium": "-l admin -P /usr/share/wordlists/rockyou.txt TARGET ssh", "high": "-L users.txt -P pass.txt TARGET ssh", "stress": "-L users.txt -P pass_big.txt TARGET ssh -t 10"}
    },
    "web_nikto": {
        "name": "Web Vulnerability Scan",
        "tool": "nikto",
        "description": "Scan vulnérabilités web",
        "intensity": {"low": "-h TARGET -majors", "medium": "-h TARGET -C all", "high": "-h TARGET -C all -majors", "stress": "-h TARGET -C all -majors -evasion 1"}
    },
    "dos_slow": {
        "name": "DoS Contrôlé (Slow)",
        "tool": "slowhttptest",
        "description": "Test DoS lent et contrôlé",
        "intensity": {"low": "-c 100 -H -i 10 -r 100 -t GET", "medium": "-c 500 -H -i 10 -r 200", "high": "-c 1000 -H -i 5 -r 500", "stress": "-c 2000 -H -i 1 -r 1000"}
    },
    "attack_chain_full": {
        "name": "Full Kill Chain",
        "tool": "chain",
        "description": "Chaîne complète: recon → brute force → exploitation → exfiltration",
        "intensity": {"low": "full", "medium": "full", "high": "full", "stress": "full"}
    }
}

JOB_KEY_PREFIX = "attack_job:"
CAMPAIGN_KEY_PREFIX = "campaign:"


def validate_target(target: str) -> bool:
    """Vérifie si la cible est dans l'allowlist."""
    if target in TARGET_ALLOWLIST:
        return True
    # Allow IPs in Docker network (simple check)
    if target.startswith("172.") or target.startswith("10.") or target.startswith("192.168."):
        return True
    return False


async def run_attack_job(job_id: str, scenario: str, target: str, intensity: str, duration: int):
    """Exécute un job d'attaque en arrière-plan."""
    try:
        redis_client.hset(f"{JOB_KEY_PREFIX}{job_id}", "status", "running")
        redis_client.hset(f"{JOB_KEY_PREFIX}{job_id}", "started_at", datetime.now(timezone.utc).isoformat())
        
        if scenario not in ATTACK_SCENARIOS:
            raise ValueError(f"Scénario {scenario} inconnu")
        
        scenario_config = ATTACK_SCENARIOS[scenario]
        cmd_args = scenario_config["intensity"].get(intensity, scenario_config["intensity"]["low"])
        
        # Construire la commande
        if scenario == "attack_chain_full":
            # Exécuter une chaîne d'attaques
            await run_attack_chain(job_id, target, intensity)
        else:
            cmd = f"{scenario_config['tool']} {cmd_args.replace('TARGET', target)}"
            redis_client.hset(f"{JOB_KEY_PREFIX}{job_id}", "command", cmd)
            
            # Exécuter la commande avec timeout
            process = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            # Lire la sortie en temps réel
            while True:
                line = await process.stdout.readline()
                if not line:
                    break
                log_line = line.decode().strip()
                redis_client.rpush(f"{JOB_KEY_PREFIX}{job_id}:logs", log_line)
                redis_client.ltrim(f"{JOB_KEY_PREFIX}{job_id}:logs", -1000, -1)  # Garder 1000 dernières lignes
            
            await process.wait()
            return_code = process.returncode
            
            redis_client.hset(f"{JOB_KEY_PREFIX}{job_id}", "return_code", str(return_code))
            redis_client.hset(f"{JOB_KEY_PREFIX}{job_id}", "completed_at", datetime.now(timezone.utc).isoformat())
            redis_client.hset(f"{JOB_KEY_PREFIX}{job_id}", "status", "completed" if return_code == 0 else "failed")
        
    except Exception as e:
        logger.error(f"Erreur job {job_id}: {e}")
        redis_client.hset(f"{JOB_KEY_PREFIX}{job_id}", "status", "error")
        redis_client.hset(f"{JOB_KEY_PREFIX}{job_id}", "error", str(e))
        redis_client.rpush(f"{JOB_KEY_PREFIX}{job_id}:logs", f"ERROR: {str(e)}")


async def run_attack_chain(job_id: str, target: str, intensity: str):
    """Exécute une chaîne d'attaque complète."""
    chain_steps = [
        ("recon_nmap", "Reconnaissance initiale"),
        ("recon_httpx", "Fingerprint HTTP"),
        ("web_ffuf", "Directory bruteforce"),
        ("bruteforce_hydra", "Brute force"),
        ("web_nikto", "Scan vulnérabilités"),
    ]
    
    for step_scenario, step_name in chain_steps:
        redis_client.rpush(f"{JOB_KEY_PREFIX}{job_id}:logs", f"[CHAIN] Début: {step_name}")
        step_job_id = f"{job_id}:{step_scenario}"
        redis_client.hset(f"{JOB_KEY_PREFIX}{job_id}", "current_step", step_name)
        
        scenario_config = ATTACK_SCENARIOS[step_scenario]
        cmd_args = scenario_config["intensity"].get(intensity, scenario_config["intensity"]["low"])
        cmd = f"{scenario_config['tool']} {cmd_args.replace('TARGET', target)}"
        
        process = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        while True:
            line = await process.stdout.readline()
            if not line:
                break
            log_line = line.decode().strip()
            redis_client.rpush(f"{JOB_KEY_PREFIX}{job_id}:logs", f"[{step_name}] {log_line}")
        
        await process.wait()
        redis_client.rpush(f"{JOB_KEY_PREFIX}{job_id}:logs", f"[CHAIN] Fin: {step_name}")
    
    redis_client.hset(f"{JOB_KEY_PREFIX}{job_id}", "status", "completed")
    redis_client.hset(f"{JOB_KEY_PREFIX}{job_id}", "completed_at", datetime.now(timezone.utc).isoformat())


@router.get("/scenarios", summary="Liste des scénarios d'attaque")
def list_scenarios(_user: User = Depends(get_current_user)):
    """Retourne la liste des scénarios disponibles."""
    return [
        {
            "id": sid,
            "name": config["name"],
            "description": config["description"],
            "tool": config["tool"],
            "intensities": list(config["intensity"].keys())
        }
        for sid, config in ATTACK_SCENARIOS.items()
    ]


@router.post("/launch", summary="Lancer une attaque")
async def launch_attack(
    scenario: str,
    target: str = "serveur-endpoint",
    intensity: str = "low",
    duration: int = 60,
    background_tasks: BackgroundTasks = None,
    _user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Lance une attaque contrôlée."""
    if not validate_target(target):
        raise HTTPException(status_code=400, detail="Cible non autorisée")
    
    if scenario not in ATTACK_SCENARIOS:
        raise HTTPException(status_code=404, detail="Scénario inconnu")
    
    if intensity not in ["low", "medium", "high", "stress"]:
        raise HTTPException(status_code=400, detail="Intensité invalide")
    
    job_id = f"job_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}_{scenario}"
    
    # Initialiser le job dans Redis
    redis_client.hset(f"{JOB_KEY_PREFIX}{job_id}", "scenario", scenario)
    redis_client.hset(f"{JOB_KEY_PREFIX}{job_id}", "target", target)
    redis_client.hset(f"{JOB_KEY_PREFIX}{job_id}", "intensity", intensity)
    redis_client.hset(f"{JOB_KEY_PREFIX}{job_id}", "status", "pending")
    redis_client.hset(f"{JOB_KEY_PREFIX}{job_id}", "created_by", _user.username)
    redis_client.expire(f"{JOB_KEY_PREFIX}{job_id}", 3600)  # Expire après 1h
    
    # Lancer en arrière-plan
    asyncio.create_task(run_attack_job(job_id, scenario, target, intensity, duration))
    
    return {"job_id": job_id, "status": "pending", "message": "Attaque lancée"}


@router.get("/job/{job_id}", summary="Statut d'un job")
def get_job_status(job_id: str, _user: User = Depends(get_current_user)):
    """Récupère le statut d'un job d'attaque."""
    job_data = redis_client.hgetall(f"{JOB_KEY_PREFIX}{job_id}")
    if not job_data:
        raise HTTPException(status_code=404, detail="Job introuvable")
    
    logs = redis_client.lrange(f"{JOB_KEY_PREFIX}{job_id}:logs", -50, -1)
    
    return {
        **job_data,
        "recent_logs": logs
    }


@router.get("/jobs", summary="Liste des jobs récents")
def list_jobs(_user: User = Depends(get_current_user)):
    """Liste tous les jobs récents."""
    keys = redis_client.keys(f"{JOB_KEY_PREFIX}*")
    jobs = []
    for key in keys:
        if key.endswith(":logs"):
            continue
        job_data = redis_client.hgetall(key)
        if job_data:
            job_data["job_id"] = key.replace(JOB_KEY_PREFIX, "")
            jobs.append(job_data)
    return sorted(jobs, key=lambda x: x.get("started_at", ""), reverse=True)[:20]


@router.post("/stop/{job_id}", summary="Arrêter un job")
def stop_job(job_id: str, _user: User = Depends(get_current_user)):
    """Arrête un job d'attaque en cours."""
    job_data = redis_client.hgetall(f"{JOB_KEY_PREFIX}{job_id}")
    if not job_data:
        raise HTTPException(status_code=404, detail="Job introuvable")
    
    # Marquer comme arrêté (le processus sera tué par le watcher)
    redis_client.hset(f"{JOB_KEY_PREFIX}{job_id}", "status", "stopped")
    redis_client.hset(f"{JOB_KEY_PREFIX}{job_id}", "stopped_at", datetime.now(timezone.utc).isoformat())
    redis_client.rpush(f"{JOB_KEY_PREFIX}{job_id}:logs", "ARRÊT MANUEL DEMANDÉ")
    
    return {"status": "stopped", "message": "Job arrêté"}


@router.post("/stop-all", summary="Arrêter tous les jobs")
def stop_all_jobs(_user: User = Depends(get_current_user)):
    """Arrête tous les jobs en cours."""
    keys = redis_client.keys(f"{JOB_KEY_PREFIX}*")
    stopped = 0
    for key in keys:
        if key.endswith(":logs"):
            continue
        job_data = redis_client.hgetall(key)
        if job_data.get("status") in ["running", "pending"]:
            redis_client.hset(key, "status", "stopped")
            redis_client.hset(key, "stopped_at", datetime.now(timezone.utc).isoformat())
            stopped += 1
    
    return {"stopped_count": stopped, "message": f"{stopped} jobs arrêtés"}


@router.get("/targets", summary="Cibles autorisées")
def list_targets(_user: User = Depends(get_current_user)):
    """Retourne la liste des cibles autorisées."""
    return {"targets": TARGET_ALLOWLIST, "note": "Seules ces cibles sont autorisées"}
