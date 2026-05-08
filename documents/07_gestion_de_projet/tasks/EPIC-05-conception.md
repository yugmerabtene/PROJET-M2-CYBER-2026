# Document de Conception - EPIC-05 : Corrélation et Enrichissement Analyste

**Date**: 8 Mai 2026  
**Statut**: Prêt pour implémentation  
**Sprint cible**: Sprint 5 (final)  
**Priorité globale**: P2 (mais enrichissement P1 pour Sprint 5)

---

## 1. État des lieux (Sprint 4 - existant)

### 1.1 Ce qui existe (implémenté)
| Composant | Description | Localisation |
|---|---|---|
| **Modèles** | `CorrelationGroup` + `CorrelatedEvent` | `app/correlation/models.py` |
| **Types actifs** | `ip_source`, `temporal_burst` | `service.py:35, 115` |
| **Score de risque temporel** | `_calculate_temporal_risk_score()` (0-100) | `service.py:158-195` |
| **ML Integration** | `IsolationForest` + `enrich_with_ml_scores()` | `ml/service.py`, `service.py:254-303` |
| **Endpoints** | 7 endpoints (liste, détail, run, resolve, ML) | `correlation/routes.py` |
| **Frontend** | Cartes cliquables + modal détail | `app.js:renderCorrelations()` |

### 1.2 Limites identifiées
1. **Relation Alert-Correlation** : `alert_ids` est un JSON, pas une vraie FK → Requêtes lentes, pas de jointure SQL
2. **Pas de corrélation par hostname** : L'agent envoie `hostname`, mais pas utilisé pour corréler
3. **Score ML isolé** : Pas intégré dans le score composite initial
4. **Pas de détection de chaîne d'attaque** : Scan → Bruteforce → Escalade non détectés comme suite logique
5. **Timeline manuelle** : Pas de vue chronologique visuelle
6. **Pas de corrélation par plage d'IP** : Réseaux /24, /16 non traités

---

## 2. Nouveaux Types de Corrélation

### 2.1 `ip_source` (existant - à améliorer)
```
Logique : Tous événements avec même source_ip
Amélioration : Inclure le hostname depuis la table assets
Score actuel : basé sur le nombre d'événements uniquement
Nouveau score : + diversité types + ML score
```

### 2.2 `temporal_burst` (existant - à améliorer)
```
Logique : Événements dans une fenêtre temporelle (défaut 10min)
Amélioration : Score ML intégré au risque temporel
Nouveau : Détection de "calme avant la tempête" (période d'activité nulle puis burst)
```

### 2.3 `hostname_match` (NOUVEAU - P2)
```
Logique : Regrouper par hostname cible (depuis agents ou table assets)
Utilité : Si un hostname résout vers plusieurs IPs, corréler quand même
Implémentation : JOIN avec table assets ON hostname
Données sources : agent.hostname, heartbeat.hostname
```

### 2.4 `attack_chain` (NOUVEAU - P2)
```
Logique : Détecter une séquence logique d'attaque
Séquence typique : port_scan → brute_force → privilege_escalation → data_exfiltration
Implémentation : State machine avec timeouts
Exemple : Si scan détecté à T, puis bruteforce à T+5min → créer chaîne
```

### 2.5 `ip_range` (NOUVEAU - P3)
```
Logique : Regrouper par plage CIDR (/24, /16)
Utilité : Attaquant qui change d'IP dans une plage
Implémentation : Calcul de hash CIDR depuis source_ip
Exemple : 192.168.1.10 et 192.168.1.50 → même groupe /24
```

---

## 3. Score Composite de Corrélation (0-100)

### 3.1 Formule proposée
```python
Score_final = (
    (score_risque_temporel * 0.35) +      # 0-100
    (score_ml_normalisé * 100 * 0.25) +   # 0-100 (IsolationForest)
    (score_diversite * 0.20) +             # 0-100 (types + IPs + ports)
    (score_severite * 0.20)                # 0-100 (basé sur distribution)
)
```

### 3.2 Nouveaux facteurs de score

**Score de diversité (0-100) :**
- Types d'événements uniques : `min(nb_types * 10, 30)`
- IPs sources uniques : `min(nb_sources * 5, 20)`
- IPs cibles uniques : `min(nb_cibles * 5, 20)`
- Ports uniques (si disponibles) : `min(nb_ports * 3, 30)`

**Bonus/Malus :**
- Chaîne d'attaque détectée : +20
- Score ML > 0.8 : +15
- Présence `critical` events : +10 par event (max +30)
- Même hostname, IPs différentes : +15

### 3.3 Implémentation dans `service.py`

```python
def calculate_composite_score(
    events: list[dict],
    temporal_score: int,
    ml_scores: list[float] | None = None,
    group_type: str = "unknown"
) -> dict:
    """
    Retourne : {
        "composite_score": int (0-100),
        "temporal_weight": 0.35,
        "ml_weight": 0.25,
        "diversity_weight": 0.20,
        "severity_weight": 0.20,
        "breakdown": { ... }
    }
    """
    # 1. Temporal score (déjà calculé)
    temporal_contribution = temporal_score * 0.35

    # 2. ML score (moyenne des scores d'anomalie)
    ml_avg = sum(ml_scores) / len(ml_scores) if ml_scores else 0.0
    ml_contribution = ml_avg * 100 * 0.25

    # 3. Diversity score
    unique_types = len(set(e.get("event_type") for e in events))
    unique_sources = len(set(e.get("source_ip") for e in events if e.get("source_ip")))
    unique_targets = len(set(e.get("target_ip") for e in events if e.get("target_ip")))
    
    diversity_score = min(unique_types * 10, 30) + min(unique_sources * 5, 20) + min(unique_targets * 5, 20)
    diversity_contribution = min(diversity_score, 100) * 0.20

    # 4. Severity score
    severity_weights = {"critical": 25, "high": 18, "medium": 10, "low": 4}
    severity_score = min(sum(severity_weights.get(e.get("severity"), 1) for e in events), 30)
    severity_contribution = severity_score * 0.20

    composite = min(int(temporal_contribution + ml_contribution + diversity_contribution + severity_contribution), 100)

    return {
        "composite_score": composite,
        "breakdown": {
            "temporal": {"score": temporal_score, "weight": 0.35, "contribution": temporal_contribution},
            "ml": {"avg_score": round(ml_avg, 3), "weight": 0.25, "contribution": ml_contribution},
            "diversity": {"score": diversity_score, "weight": 0.20, "contribution": diversity_contribution},
            "severity": {"score": severity_score, "weight": 0.20, "contribution": severity_contribution},
        }
    }
```

---

## 4. Modifications Base de Données

### 4.1 Table `correlation_groups` (mise à jour)

```python
class CorrelationGroup(Base):
    __tablename__ = "correlation_groups"

    # Champs existants (à conserver)
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    group_type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    source_ip: Mapped[str] = mapped_column(String(45), nullable=True, index=True)
    target_ip: Mapped[str] = mapped_column(String(45), nullable=True)
    severity: Mapped[str] = mapped_column(String(16), nullable=False, default="medium")
    event_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    first_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    is_resolved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # ========= NOUVEAUX CHAMPS =========
    # Score composite (0-100)
    correlation_score: Mapped[float] = mapped_column(default=0.0, nullable=False, index=True)
    
    # Pour hostname_match
    hostname: Mapped[str] = mapped_column(String(255), nullable=True, index=True)
    
    # Pour ip_range
    ip_cidr: Mapped[str] = mapped_column(String(20), nullable=True, index=True)  # ex: "192.168.1.0/24"
    
    # Pour attack_chain (type de chaîne détectée)
    attack_chain_type: Mapped[str] = mapped_column(String(64), nullable=True)
    
    # Score breakdown (JSON for transparency)
    score_breakdown: Mapped[dict] = mapped_column(JSON, nullable=True)
    
    # Relations (remplace alert_ids JSON)
    alerts: Mapped[list["Alert"]] = relationship(
        back_populates="correlation_groups",
        secondary="alert_correlation_association"
    )

    events: Mapped[list["CorrelatedEvent"]] = relationship(
        back_populates="group", 
        lazy="selectin", 
        cascade="all, delete-orphan"
    )
```

### 4.2 Table `correlated_events` (mise à jour)

```python
class CorrelatedEvent(Base):
    __tablename__ = "correlated_events"

    # Champs existants
    id: Mapped[int] = mapped_column(primary_key=True)
    group_id: Mapped[int] = mapped_column(Integer, ForeignKey("correlation_groups.id"), nullable=False, index=True)
    telemetry_event_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    source_ip: Mapped[str] = mapped_column(String(45), nullable=True, index=True)
    target_ip: Mapped[str] = mapped_column(String(45), nullable=True)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    severity: Mapped[str] = mapped_column(String(16), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=True)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    raw_payload: Mapped[dict] = mapped_column(JSON, nullable=True)

    # ========= NOUVEAUX CHAMPS =========
    # Ordre dans la timeline (séquence)
    sequence_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Score ML individuel (pour cet événement dans le groupe)
    ml_anomaly_score: Mapped[float] = mapped_column(default=0.0, nullable=False)
    
    group: Mapped["CorrelationGroup"] = relationship(back_populates="events")
```

### 4.3 Nouvelle table d'association Alert <-> CorrelationGroup

```python
class AlertCorrelationAssociation(Base):
    __tablename__ = "alert_correlation_assoc"
    
    alert_id: Mapped[int] = mapped_column(Integer, ForeignKey("alerts.id"), primary_key=True)
    correlation_group_id: Mapped[int] = mapped_column(Integer, ForeignKey("correlation_groups.id"), primary_key=True)
    linked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        default=lambda: datetime.now(timezone.utc)
    )
```

### 4.4 Modèle `Alert` (mise à jour)

```python
class Alert(Base):
    __tablename__ = "alerts"
    
    # ... champs existants ...
    
    # NOUVEAU : Relation many-to-many avec CorrelationGroup
    correlation_groups: Mapped[list["CorrelationGroup"]] = relationship(
        back_populates="alerts",
        secondary="alert_correlation_assoc"
    )
```

---

## 5. API Enrichie

### 5.1 Endpoints existants (à enrichir)

| Endpoint | Modification | Priorité |
|---|---|---|
| `GET /correlation` | Ajouter `min_score` param, tri par `correlation_score` | P2 |
| `GET /correlation/{id}` | Ajouter `composite_score` + `score_breakdown` | P2 |
| `GET /correlation/{id}/events` | Ajouter `sequence_order`, tri chronologique | P2 |
| `POST /correlation/run-ip` | Calculer `correlation_score` composite | P2 |
| `POST /correlation/run-temporal` | Intégrer ML + composite score | P2 |

### 5.2 Nouveaux endpoints

```python
# ========= NOUVEAUX ENDPOINTS =========

@router.post("/run-hostname", summary="Corrélation par hostname")
def run_hostname_correlation(
    events: list[dict],
    min_events: int = Query(3, ge=1),
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
):
    """Regroupe les événements par hostname cible."""
    return correlate_by_hostname(db, events, min_events)


@router.post("/run-attack-chain", summary="Détecter chaînes d'attaque")
def run_attack_chain_detection(
    events: list[dict] | None = None,
    use_database: bool = True,
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
):
    """Détecte séquences logiques (scan → bruteforce → ...)"""
    if events is None and use_database:
        events = get_events_from_db(db)
    return detect_attack_chains(db, events)


@router.post("/run-ip-range", summary="Corrélation par plage d'IP")
def run_ip_range_correlation(
    events: list[dict],
    cidr_prefix: int = Query(24, ge=8, le=32),
    min_events: int = Query(3, ge=1),
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
):
    """Regroupe par plage CIDR (/24, /16, ...)"""
    return correlate_by_ip_range(db, events, cidr_prefix, min_events)


@router.get("/{group_id}/timeline", summary="Timeline détaillée")
def get_correlation_timeline(
    group_id: int,
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
):
    """Retourne timeline avec séquençage et scores ML."""
    group = get_group_by_id(db, group_id)
    if not group:
        raise HTTPException(404, "Group not found")
    events = get_group_events_with_sequence(db, group_id)
    return {
        "group_id": group_id,
        "timeline": events,
        "score_breakdown": group.score_breakdown,
    }


@router.post("/manual-group", summary="Création manuelle par analyste")
def manual_correlation_group(
    event_ids: list[int],
    group_name: str,
    group_type: str = "manual",
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
):
    """Permet à l'analyste de regrouper manuellement des événements."""
    return create_manual_group(db, event_ids, group_name, group_type, _user.username)
```

---

## 6. Frontend - Visualisation et Timeline

### 6.1 Timeline View (Nouveau composant)

**Approche technique** : SVG natif (pas de bibliothèque externe, contrainte Alpine.js + HTMX + Tailwind)

```html
<!-- Exemple de structure timeline -->
<div class="timeline-container bg-soc-bg rounded-lg p-4 border border-soc-border">
    <h4 class="text-sm font-medium text-white mb-4">Timeline de corrélation</h4>
    
    <div class="relative">
        <!-- Ligne verticale -->
        <div class="absolute left-4 top-0 bottom-0 w-0.5 bg-soc-border"></div>
        
        <!-- Événements -->
        <template x-for="(event, index) in timelineEvents" :key="event.id">
            <div class="relative pl-10 pb-6">
                <!-- Point sur la timeline -->
                <div class="absolute left-2 w-4 h-4 rounded-full border-2 border-soc-accent bg-soc-bg"
                     :class="event.severity === 'critical' ? 'border-soc-danger bg-soc-danger/20' : ''">
                </div>
                
                <!-- Contenu -->
                <div class="bg-soc-card rounded-lg p-3 border border-soc-border">
                    <div class="flex items-center gap-2 mb-1">
                        <span class="text-xs text-soc-muted">#<span x-text="index + 1"></span></span>
                        <span class="text-sm font-medium text-white" x-text="event.event_type"></span>
                        <span class="text-xs px-2 py-0.5 rounded bg-soc-card text-soc-muted" x-text="event.severity"></span>
                    </div>
                    <p class="text-xs text-soc-muted" x-text="event.message"></p>
                    <p class="text-xs text-soc-muted mt-1" x-text="formatDate(event.observed_at)"></p>
                </div>
            </div>
        </template>
    </div>
</div>
```

### 6.2 Score Gauge (Nouveau composant)

```html
<!-- Jauge circulaire pour score composite -->
<div class="score-gauge relative w-32 h-32">
    <svg class="transform -rotate-90" width="128" height="128" viewBox="0 0 128 128">
        <!-- Fond -->
        <circle cx="64" cy="64" r="56" fill="none" stroke="#1e293b" stroke-width="12"/>
        <!-- Score (calculé dynamiquement) -->
        <circle cx="64" cy="64" r="56" fill="none" 
                :stroke="scoreColor" 
                stroke-width="12" 
                :stroke-dasharray="scoreArc + ' ' + (352 - scoreArc)"
                stroke-linecap="round"/>
    </svg>
    <div class="absolute inset-0 flex items-center justify-center">
        <span class="text-2xl font-bold" :class="scoreTextColor" x-text="compositeScore"></span>
    </div>
</div>

<script>
// Calcul du score arc pour SVG
function updateGauge(score) {
    const circumference = 2 * Math.PI * 56; // r=56
    const scoreArc = (score / 100) * circumference;
    const scoreColor = score > 70 ? '#ef4444' : score > 40 ? '#f59e0b' : '#10b981';
    return { scoreArc, scoreColor };
}
</script>
```

### 6.3 Attack Chain Diagram (Nouveau composant)

```html
<!-- Diagramme de chaîne d'attaque -->
<div class="attack-chain flex items-center gap-2 overflow-x-auto py-4">
    <template x-for="(step, idx) in attackChain">
        <div class="flex items-center">
            <div class="flex flex-col items-center min-w-[100px]">
                <div class="w-12 h-12 rounded-full flex items-center justify-center"
                     :class="step.detected ? 'bg-soc-danger/20 border-2 border-soc-danger' : 'bg-soc-bg border-2 border-soc-border'">
                    <span class="text-xs font-bold" x-text="idx + 1"></span>
                </div>
                <span class="text-xs text-soc-muted mt-1" x-text="step.event_type"></span>
            </div>
            <template x-if="idx < attackChain.length - 1">
                <div class="flex-1 h-0.5 bg-soc-border min-w-[50px]"></div>
            </template>
        </div>
    </template>
</div>
```

---

## 7. Détection de Chaîne d'Attaque (Attack Chain)

### 7.1 Logique de détection

```python
ATTACK_CHAIN_PATTERNS = {
    "recon_to_exploit": {
        "sequence": ["network_scan", "port_scan", "brute_force", "privilege_escalation"],
        "max_time_between_steps": 300,  # 5 minutes
        "description": "Reconnaissance → Exploitation"
    },
    "data_breach": {
        "sequence": ["brute_force", "suspicious_login", "privilege_escalation", "data_exfiltration"],
        "max_time_between_steps": 600,  # 10 minutes
        "description": "Brute force → Exfiltration de données"
    },
    "lateral_movement": {
        "sequence": ["compromised_host", "lateral_movement", "c2_communication"],
        "max_time_between_steps": 180,
        "description": "Mouvement latéral → C2"
    }
}

def detect_attack_chains(db: Session, events: list[dict]) -> list[CorrelationGroup]:
    """Détecte des séquences logiques dans les événements."""
    sorted_events = sorted(events, key=lambda e: e.get("observed_at", ""))
    groups = []
    
    for pattern_name, pattern in ATTACK_CHAIN_PATTERNS.items():
        sequences = find_sequences(sorted_events, pattern["sequence"], pattern["max_time_between_steps"])
        
        for seq in sequences:
            # Créer un groupe de type attack_chain
            group = CorrelationGroup(
                name=f"Chaîne d'attaque: {pattern['description']}",
                group_type="attack_chain",
                attack_chain_type=pattern_name,
                description=f"Séquence détectée: {' → '.join(pattern['sequence'])}",
                severity=_calculate_chain_severity(seq),
                event_count=len(seq),
                first_seen=_parse_dt(seq[0].get("observed_at")),
                last_seen=_parse_dt(seq[-1].get("observed_at")),
                correlation_score=calculate_chain_score(seq, pattern),
            )
            db.add(group)
            db.flush()
            
            # Ajouter les événements avec ordre de séquence
            for idx, evt in enumerate(seq):
                correlated = CorrelatedEvent(
                    group_id=group.id,
                    sequence_order=idx,
                    # ... autres champs
                )
                db.add(correlated)
            
            groups.append(group)
    
    db.commit()
    return groups


def find_sequences(events: list[dict], pattern: list[str], max_time_diff: int) -> list[list[dict]]:
    """Trouve des séquences correspondant au pattern."""
    sequences = []
    n = len(pattern)
    
    for i in range(len(events) - n + 1):
        sequence = []
        valid = True
        
        for j in range(n):
            if events[i + j].get("event_type") != pattern[j]:
                valid = False
                break
            if j > 0:
                # Vérifier le temps entre les étapes
                t1 = _parse_dt(events[i + j - 1].get("observed_at"))
                t2 = _parse_dt(events[i + j].get("observed_at"))
                if (t2 - t1).total_seconds() > max_time_diff:
                    valid = False
                    break
            sequence.append(events[i + j])
        
        if valid and sequence:
            sequences.append(sequence)
    
    return sequences
```

---

## 8. Plan d'Implémentation (Sprint 5 - 1 semaine)

### 8.1 Priorisation

| US | Description | Tâches | SP | Statut |
|---|---|---|---:|---|
| **US-05.1** | Corrélation IP existante | Enrichir avec score composite + ML | 5 | ✅ Fait (à améliorer) |
| **US-05.2** | Corrélation temporelle | Intégrer ML + composite score | 5 | ✅ Fait (à améliorer) |
| **US-05.3** | Vue corrélation | Modal détail (✅ fait) + Timeline (🕕) | 5 | En cours |
| **US-05.4** | Corrélation hostname | Nouveau type `hostname_match` | 5 | À faire |
| **US-05.5** | Chaînes d'attaque | `attack_chain` + diagramme | 8 | À faire |
| **US-05.6** | Timeline visualisation | SVG natif + séquençage | 5 | À faire |
| **US-05.7** | Score composite | Implémentation formule + gauge | 5 | À faire |
| **US-05.8** | Relation Alert-Correlation | FK propre + endpoints | 3 | À faire |

### 8.2 Diagramme de Gantt (Sprint 5 - 1 semaine)

```
Jour 1-2 : Modifications DB + Migration
Jour 2-3 : Score composite + Intégration ML
Jour 3-4 : Attack chain + Hostname correlation
Jour 4-5 : Timeline frontend + Visualisation
Jour 5-7 : Tests + Documentation + Validation
```

---

## 9. Tests et Validation

### 9.1 Scénarios de test

| ID | Scénario | Attendu | Priorité |
|---|---|---|---|
| TC-05.1 | Envoyer 10 événements même IP | Groupe `ip_source` créé, score > 50 | P2 |
| TC-05.2 | Burst 20 événements en 5min | Groupe `temporal_burst`, score composite calculé | P2 |
| TC-05.3 | Séquence scan → bruteforce | Groupe `attack_chain` détecté | P2 |
| TC-05.4 | 5 événements hostname cible | Groupe `hostname_match` créé | P3 |
| TC-05.5 | Cliquer corrélation → Timeline | Timeline affichée avec séquence | P2 |
| TC-05.6 | Voir score composite | Jauge + décomposition visible | P2 |

### 9.2 Performance

- **Objectif** : `GET /correlation` < 200ms pour 100 groupes
- **Objectif** : Calcul score composite < 50ms pour 100 événements
- **Objectif** : Timeline render < 100ms pour 50 événements

---

## 10. Décision Requise (Avant Implémentation)

1. **Timeline** : SVG natif (recommandé) ou bibliothèque légère (vis.js) ?
2. **Score composite** : Garder 4 facteurs (temporel, ML, diversité, sévérité) ou simplifier ?
3. **Attack chain** : Regex-based (plus simple) ou state machine (plus robuste) ?
4. **Relation Alert-Correlation** : Migration lourde (FK) ou garder JSON avec index ?
5. **Hostname correlation** : Via table `assets` (sync nécessaire) ou via événements bruts ?

---

## 11. Références

- EPIC-05 dans le [Product Backlog](./rendu_principal.md#8-product-backlog-structuré)
- User Stories [US-05.1 à US-05.3](./rendu_principal.md#10-user-stories-et-tasks-mvp)
- Architecture [§5 Logique](./rendu_principal.md#5-architecture-logicielle)
- Modèles actuels : `app/correlation/models.py`
- Service actuel : `app/correlation/service.py`
- ML Service : `app/ml/service.py`
