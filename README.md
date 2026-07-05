# bim-audit-engine

Cœur d'un **moteur d'audit BIM générique**, extrait de
[`audit-bim-i3f`](https://github.com/Slimouzi/audit-bim-i3f). Fournit **uniquement** :

- un **protocole de règle** `Rule` (générique, contravariant) ;
- une **boucle d'exécution** `run_audit` (règles **injectables**, tri déterministe) ;
- un conteneur de résultat `AuditResult` (générique sur le catalogue & la phase).

Il **ne contient aucune règle métier**, aucun schéma de catalogue, aucune phase
concrète, aucun helper. L'appelant injecte son catalogue, sa phase et son jeu de
règles. Dépend de [`bim-core`](https://github.com/Slimouzi/bim-core) **uniquement**
(`Finding`/`Severity`/`Theme`/`ErrorType` + `ModelSnapshot`).

## API

```python
from bim_audit_engine import Rule, run_audit, AuditResult
```

- `Rule[CatalogT, PhaseT]` — `Protocol` : `(snap, catalog, phase) -> list[Finding]`.
  `CatalogT`/`PhaseT` sont **contravariants** (entrée seulement).
- `run_audit(snap, catalog, phase, rules) -> AuditResult[CatalogT, PhaseT]` —
  exécute les `rules` **dans l'ordre**, agrège, trie (sévérité décroissante →
  thème → type d'erreur → classe IFC → nom). **Garantie** : pour une **même
  séquence ordonnée de règles**, la sortie est reproductible. Le tri est
  **stable**, pas indépendant de l'ordre : à clé égale, deux findings de règles
  distinctes suivent l'ordre des règles.
- `AuditResult[CatalogT, PhaseT]` — `count_by_*`, `filter(...)`,
  `conformity_rate()`, `summary()` (tolère une phase **non-Enum**).

## Frontière (v0.1 minimal)

Le catalogue et la phase sont **génériques par paramètres de type** : le package
n'impose ni `RequirementsCatalog` ni `BIMPhase` (ils portent des concepts métier
et restent chez l'appelant). Les règles concrètes, les schémas de catalogue et les
helpers d'accès Pset/validation ne font **pas** partie de cette version (extraction
ultérieure via un package dédié).

## Installation

```bash
git clone https://github.com/Slimouzi/bim-audit-engine.git
cd bim-audit-engine
python -m venv .venv && source .venv/bin/activate
# bim-core n'est pas publié sur PyPI : préinstaller depuis son tag Git.
pip install "git+https://github.com/Slimouzi/bim-core.git@bim-core-v0.1.0"
pip install -e ".[dev]"
```

## Exemple

```python
from enum import Enum
from bim_audit_engine import run_audit

class Phase(str, Enum):
    AVP = "AVP"

def my_rule(snap, catalog, phase):
    return []  # -> list[Finding] (bim-core)

result = run_audit(snapshot, my_catalog, Phase.AVP, rules=[my_rule])
print(result.summary())
```

## Tests

```bash
pytest -q
```

Exécute `run_audit` avec **phase `str`, phase `Enum` et phase objet**, un
**catalogue factice**, **zéro** et **plusieurs** règles ; vérifie le déterminisme
pour une même séquence de règles, la stabilité du tri (à clé égale → ordre des
règles), les agrégats, la **sérialisation JSON** de `summary()` (phase objet), et
la **pureté** (aucun `audit_bim`/réseau à l'import). Offline.

## Licence

Apache-2.0 — © Stanislas Limouzi / BIMData.
