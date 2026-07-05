"""Boucle d'exécution d'audit — **règles injectables**, tri déterministe.

Le moteur ne fait aucune analyse : il exécute une **liste de règles injectée**
(protocole :class:`Rule`), agrège leurs ``Finding`` et les trie de façon
**déterministe**, puis empaquette le tout dans un
:class:`bim_audit_engine.result.AuditResult`.

Générique sur le catalogue et la phase : l'appelant (p.ex. `audit-bim-i3f`) passe
son propre type de catalogue/phase **et** son jeu de règles. Le package ne
connaît ni `RequirementsCatalog` ni `BIMPhase`.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, TypeVar

from bim_core.findings import Finding, Severity
from bim_core.model_snapshot import ModelSnapshot

from .result import AuditResult

CatalogT = TypeVar("CatalogT")
PhaseT = TypeVar("PhaseT")

# Contravariants : ``catalog``/``phase`` n'apparaissent qu'en **entrée** d'une
# règle.
_CatalogT_contra = TypeVar("_CatalogT_contra", contravariant=True)
_PhaseT_contra = TypeVar("_PhaseT_contra", contravariant=True)


class Rule(Protocol[_CatalogT_contra, _PhaseT_contra]):
    """Une règle d'audit : ``(snapshot, catalog, phase) -> list[Finding]``.

    Contrat structurel (duck-typing) — une simple fonction module-level
    satisfait le protocole. Aucune sévérité/aucun texte n'est imposé : c'est la
    règle (côté métier) qui produit ses ``Finding``.
    """

    def __call__(
        self,
        snap: ModelSnapshot,
        catalog: _CatalogT_contra,
        phase: _PhaseT_contra,
    ) -> list[Finding]: ...


def _sort_key(f: Finding, sev_order: dict[Severity, int]) -> tuple:
    """Clé de tri déterministe : sévérité décroissante > thème > type d'erreur
    > classe IFC > nom."""
    return (
        sev_order.get(f.severity, 99),
        f.theme.value,
        f.error_type.value,
        f.ifc_type or "",
        f.name or "",
    )


def run_audit(
    snap: ModelSnapshot,
    catalog: CatalogT,
    phase: PhaseT,
    rules: Sequence[Rule[CatalogT, PhaseT]],
) -> AuditResult[CatalogT, PhaseT]:
    """Exécute les ``rules`` injectées, agrège et trie les findings.

    Args:
        snap: Photo du modèle (``bim-core``).
        catalog: Catalogue d'exigences (type au choix de l'appelant).
        phase: Phase auditée (Enum ou toute valeur).
        rules: Séquence **ordonnée** de règles ``(snap, catalog, phase) ->
            list[Finding]``. Le tri est **stable** : à clé de tri égale, les
            findings gardent leur ordre d'insertion (donc l'ordre des règles).

    Returns:
        :class:`AuditResult` — findings triés (sévérité décroissante puis thème
        puis type d'erreur puis classe IFC puis nom).

    Garantie de déterminisme : **pour une même séquence ordonnée de règles**, la
    sortie est identique d'un appel à l'autre. Le tri n'est pas indépendant de
    l'ordre des règles : deux findings de **même clé** issus de règles distinctes
    apparaissent dans l'ordre où les règles sont fournies (tri stable).
    """
    findings: list[Finding] = []
    for rule in rules:
        findings.extend(rule(snap, catalog, phase))

    sev_order = {s: i for i, s in enumerate(Severity.ordered())}
    findings.sort(key=lambda f: _sort_key(f, sev_order))

    return AuditResult(phase=phase, catalog=catalog, snapshot=snap, findings=findings)


__all__ = ["Rule", "run_audit"]
