from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
import asyncio
import json
import redis
import logging
from datetime import datetime, timezone
from pydantic import BaseModel
from urllib.request import Request, urlopen
from urllib.error import URLError

from app.core.config import settings
from app.core.deps import get_current_user, get_db
from app.auth.models import User

router = APIRouter()
logger = logging.getLogger(__name__)


class AttackLaunchRequest(BaseModel):
    scenario: str
    target: str = "serveur-endpoint"
    intensity: str = "low"
    duration: int = 60

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
        "category": "recon",
        "tool": "nmap",
        "description": "Scan de ports avec nmap",
        "intensity": {"low": "-sS -p 22,80,443 TARGET", "medium": "-sS -p 1-1000 TARGET", "high": "-sS -p- TARGET", "stress": "-sS -p- -T5 TARGET"}
    },
    "recon_httpx": {
        "name": "Reconnaissance HTTP",
        "category": "recon",
        "tool": "httpx",
        "description": "Fingerprint HTTP",
        "intensity": {"low": "-u http://TARGET -silent", "medium": "-u http://TARGET -tech-detect", "high": "-u http://TARGET -probe-all", "stress": "-u http://TARGET -probe-all -threads 100"}
    },
    "web_ffuf": {
        "name": "Directory Bruteforce",
        "category": "web",
        "tool": "ffuf",
        "description": "Fuzzing de répertoires web",
        "intensity": {"low": "-u http://TARGET/FUZZ -w /usr/share/wordlists/dirb/small.txt", "medium": "-u http://TARGET/FUZZ -w /usr/share/wordlists/dirb/common.txt", "high": "-u http://TARGET/FUZZ -w /usr/share/wordlists/dirb/big.txt", "stress": "-u http://TARGET/FUZZ -w /usr/share/wordlists/dirb/big.txt -t 100"}
    },
    "bruteforce_hydra": {
        "name": "Brute Force Hydra",
        "category": "bruteforce",
        "tool": "hydra",
        "description": "Attaque brute force contrôlée",
        "intensity": {"low": "-l admin -p admin TARGET http-post-form '/login:username=^USER^&password=^PASS^:F=Invalid credentials'", "medium": "-l admin -P /usr/share/wordlists/rockyou.txt TARGET http-post-form '/login:username=^USER^&password=^PASS^:F=Invalid credentials'", "high": "-L users.txt -P pass.txt TARGET http-post-form '/login:username=^USER^&password=^PASS^:F=Invalid credentials'", "stress": "-L users.txt -P pass_big.txt TARGET http-post-form '/login:username=^USER^&password=^PASS^:F=Invalid credentials' -t 10"}
    },
    "web_nikto": {
        "name": "Web Vulnerability Scan",
        "category": "web",
        "tool": "nikto",
        "description": "Scan vulnérabilités web",
        "intensity": {"low": "-h http://TARGET -maxtime 30", "medium": "-h http://TARGET -C all -maxtime 45", "high": "-h http://TARGET -C all -maxtime 60", "stress": "-h http://TARGET -C all -evasion 1 -maxtime 60"}
    },
    "dos_slow": {
        "name": "DoS Contrôlé (Slow)",
        "category": "dos",
        "tool": "slowhttptest",
        "description": "Test DoS lent et contrôlé",
        "intensity": {"low": "-c 100 -H -i 10 -r 100 -t GET", "medium": "-c 500 -H -i 10 -r 200", "high": "-c 1000 -H -i 5 -r 500", "stress": "-c 2000 -H -i 1 -r 1000"}
    },
    "attack_chain_full": {
        "name": "Full Kill Chain",
        "category": "kill-chain",
        "tool": "chain",
        "description": "Chaîne complète: recon → brute force → exploitation → exfiltration",
        "intensity": {"low": "full", "medium": "full", "high": "full", "stress": "full"}
    }
}

ATTACK_PRESETS = [
    {
        "id": "preset_recon_basic",
        "name": "Recon Basique",
        "category": "recon",
        "description": "Nmap léger puis fingerprint HTTP.",
        "steps": [
            {"scenario": "recon_nmap", "intensity": "low"},
            {"scenario": "recon_httpx", "intensity": "low"},
        ],
    },
    {
        "id": "preset_web_mapping",
        "name": "Cartographie Web",
        "category": "web",
        "description": "Découverte HTTP puis fuzzing de répertoires.",
        "steps": [
            {"scenario": "recon_httpx", "intensity": "medium"},
            {"scenario": "web_ffuf", "intensity": "medium"},
        ],
    },
    {
        "id": "preset_bruteforce_validation",
        "name": "Validation Bruteforce",
        "category": "bruteforce",
        "description": "Reconnaissance légère suivie d'un bruteforce contrôlé.",
        "steps": [
            {"scenario": "recon_nmap", "intensity": "low"},
            {"scenario": "bruteforce_hydra", "intensity": "medium"},
        ],
    },
    {
        "id": "preset_web_pressure",
        "name": "Pression Web",
        "category": "dos",
        "description": "Fuzzing web puis montée de charge lente contrôlée.",
        "steps": [
            {"scenario": "web_ffuf", "intensity": "low"},
            {"scenario": "dos_slow", "intensity": "low"},
        ],
    },
    {
        "id": "preset_kill_chain_demo",
        "name": "Kill Chain Démo",
        "category": "kill-chain",
        "description": "Chaîne complète pour valider corrélation et détection.",
        "steps": [
            {"scenario": "attack_chain_full", "intensity": "low"},
        ],
    },
]

JOB_KEY_PREFIX = "attack_job:"
CAMPAIGN_KEY_PREFIX = "campaign:"
ATTACKER_API_BASE = "http://serveur-attacker:9102"
ATTACKER_SCENARIO_MAP = {
    "recon_nmap": "port_scan",
    "recon_httpx": "http_recon",
    "web_ffuf": "dir_bruteforce",
    "bruteforce_hydra": "brute_force",
    "web_nikto": "web_vuln_scan",
    "dos_slow": "dos_slow",
    "attack_chain_full": "full_kill_chain",
}


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
        
        if scenario == "attack_chain_full":
            await run_attack_chain(job_id, target, intensity)
        else:
            result = await asyncio.to_thread(
                post_attacker_command,
                "/run",
                {
                    "scenario": ATTACKER_SCENARIO_MAP.get(scenario, scenario),
                    "target": target,
                    "intensity": intensity,
                    "duration": duration,
                },
            )
            cmd = result.get("command") or scenario
            redis_client.hset(f"{JOB_KEY_PREFIX}{job_id}", "command", cmd)
            for line in split_logs(result):
                redis_client.rpush(f"{JOB_KEY_PREFIX}{job_id}:logs", line)
            return_code = int(result.get("returncode", 1 if not result.get("success") else 0))
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
    result = await asyncio.to_thread(
        post_attacker_command,
        "/run-chain",
        {
            "chain_id": ATTACKER_SCENARIO_MAP.get("attack_chain_full", "full_kill_chain"),
            "target": target,
            "intensity": intensity,
            "duration": 60,
        },
    )
    for entry in result if isinstance(result, list) else []:
        redis_client.rpush(f"{JOB_KEY_PREFIX}{job_id}:logs", f"[{entry.get('scenario','step')}] {entry.get('output','')}")
    success = bool(result) and all(entry.get("success") for entry in result if isinstance(entry, dict) and "success" in entry)
    redis_client.hset(f"{JOB_KEY_PREFIX}{job_id}", "status", "completed" if success else "failed")
    redis_client.hset(f"{JOB_KEY_PREFIX}{job_id}", "completed_at", datetime.now(timezone.utc).isoformat())


def post_attacker_command(path: str, payload: dict) -> dict | list:
    body = json.dumps(payload).encode("utf-8")
    req = Request(f"{ATTACKER_API_BASE}{path}", data=body, method="POST")
    req.add_header("Content-Type", "application/json")
    try:
        with urlopen(req, timeout=max(int(payload.get("duration", 60)) + 10, 30)) as resp:  # nosec B310
            return json.loads(resp.read().decode("utf-8"))
    except URLError as exc:
        return {"success": False, "returncode": 1, "output": f"Attacker API error: {exc}", "command": payload.get('scenario') or payload.get('chain_id')}
    except Exception as exc:
        return {"success": False, "returncode": 1, "output": f"Unexpected attacker error: {exc}", "command": payload.get('scenario') or payload.get('chain_id')}


def split_logs(result: dict) -> list[str]:
    output = result.get("output") or ""
    lines = [line for line in str(output).splitlines() if line.strip()]
    if not lines:
        lines = [json.dumps(result)]
    return lines[:200]


@router.get("/scenarios", summary="Liste des scénarios d'attaque")
def list_scenarios(_user: User = Depends(get_current_user)):
    """Retourne la liste des scénarios disponibles."""
    return [
        {
            "id": sid,
            "name": config["name"],
            "category": config.get("category", "other"),
            "description": config["description"],
            "tool": config["tool"],
            "intensities": list(config["intensity"].keys())
        }
        for sid, config in ATTACK_SCENARIOS.items()
    ]


@router.get("/presets", summary="Liste des presets d'attaque")
def list_presets(_user: User = Depends(get_current_user)):
    return ATTACK_PRESETS


@router.post("/launch", summary="Lancer une attaque")
async def launch_attack(
    payload: AttackLaunchRequest,
    background_tasks: BackgroundTasks = None,
    _user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Lance une attaque contrôlée."""
    scenario = payload.scenario
    target = payload.target
    intensity = payload.intensity
    duration = payload.duration

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
