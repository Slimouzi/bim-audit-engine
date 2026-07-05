"""bim-audit-engine — cœur d'un moteur d'audit BIM **générique**.

Fournit **uniquement** : le protocole de règle :class:`Rule` (générique,
contravariant), la boucle d'exécution :func:`run_audit` (règles **injectables**,
tri déterministe) et le conteneur de résultat :class:`AuditResult` (générique sur
le catalogue & la phase).

Ne contient **aucune règle métier**, aucun schéma de catalogue, aucune phase
concrète, aucun helper : l'appelant (p.ex. ``audit-bim-i3f``) injecte son
catalogue, sa phase et son jeu de règles. Dépend de ``bim-core`` uniquement
(``Finding``/``Severity``/``Theme``/``ErrorType`` + ``ModelSnapshot``).
"""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version

from .engine import Rule, run_audit
from .result import AuditResult

__all__ = ["Rule", "run_audit", "AuditResult"]

try:
    __version__ = version("bim-audit-engine")
except PackageNotFoundError:  # pragma: no cover — package non installé (source tree)
    __version__ = "0.0.0+unknown"
