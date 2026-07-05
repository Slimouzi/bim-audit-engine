"""``AuditResult`` — conteneur générique du résultat d'audit.

Agrégat immuable produit par :func:`bim_audit_engine.engine.run_audit` : contexte
(phase, catalogue, snapshot), anomalies (``findings``) et statistiques dérivées.

**Générique** sur le catalogue et la phase (``AuditResult[CatalogT, PhaseT]``) :
le moteur ne connaît ni le type concret du catalogue ni celui de la phase. Les
statistiques ne dépendent que des contrats ``bim-core`` (``Finding``/``Severity``)
et de ``ModelSnapshot``.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import Generic, TypeVar

from bim_core.findings import Finding, Severity
from bim_core.model_snapshot import ModelSnapshot

CatalogT = TypeVar("CatalogT")
PhaseT = TypeVar("PhaseT")


def _phase_value(phase: object) -> object:
    """Valeur d'affichage d'une phase : ``.value`` d'un Enum si disponible,
    sinon la valeur brute (ex. une phase ``str`` factice ne casse pas)."""
    return getattr(phase, "value", phase)


@dataclass
class AuditResult(Generic[CatalogT, PhaseT]):
    """Résultat complet d'un audit (générique sur catalogue & phase).

    Attributes:
        phase: Phase auditée (type ``PhaseT`` — Enum ou toute valeur).
        catalog: Référentiel des exigences (type ``CatalogT``).
        snapshot: Photo du modèle (``bim-core``).
        findings: Anomalies triées (sévérité décroissante puis thème puis
            type d'erreur puis classe IFC puis nom).
    """

    phase: PhaseT
    catalog: CatalogT
    snapshot: ModelSnapshot
    findings: list[Finding] = field(default_factory=list)

    # ── Statistiques ────────────────────────────────────────────────────────

    def count_by_theme(self) -> dict[str, int]:
        """Compte les findings par thème (``{theme_value: count}``)."""
        return dict(Counter(f.theme.value for f in self.findings))

    def count_by_severity(self) -> dict[str, int]:
        """Compte les findings par sévérité (CRITICAL/HIGH/MEDIUM/LOW/INFO)."""
        return dict(Counter(f.severity.value for f in self.findings))

    def count_by_error_type(self) -> dict[str, int]:
        """Compte les findings par type d'erreur (``{error_type_value: count}``)."""
        return dict(Counter(f.error_type.value for f in self.findings))

    def count_by_ifc_type(self) -> dict[str, int]:
        """Compte par classe IFC (anomalies sans ``ifc_type`` sous ``"?"``)."""
        return dict(Counter((f.ifc_type or "?") for f in self.findings))

    def filter(
        self,
        *,
        theme: str | None = None,
        severity: str | None = None,
        error_type: str | None = None,
        ifc_type: str | None = None,
    ) -> list[Finding]:
        """Filtre les findings sur 1+ critères combinés en ET (ordre préservé)."""
        out = list(self.findings)
        if theme:
            out = [f for f in out if f.theme.value == theme]
        if severity:
            out = [f for f in out if f.severity.value == severity]
        if error_type:
            out = [f for f in out if f.error_type.value == error_type]
        if ifc_type:
            out = [f for f in out if (f.ifc_type or "") == ifc_type]
        return out

    def conformity_rate(self) -> float:
        """Taux de conformité pondéré (indicatif) dans ``[0, 1]``.

        ``1 - (anomalies_pondérées / (n_éléments × 3))``, plafonné. Poids :
        CRITICAL 5, HIGH 3, MEDIUM 1, LOW 0.3, INFO 0.
        """
        weights = {
            Severity.CRITICAL: 5,
            Severity.HIGH: 3,
            Severity.MEDIUM: 1,
            Severity.LOW: 0.3,
            Severity.INFO: 0.0,
        }
        n_elements = max(1, len(self.snapshot.element_by_uuid))
        weighted = sum(weights.get(f.severity, 1) for f in self.findings)
        return max(0.0, min(1.0, 1.0 - (weighted / (n_elements * 3))))

    def summary(self) -> dict:
        """Résumé compact JSON-sérialisable.

        ``phase`` tolère une valeur non-Enum (valeur d'Enum si disponible,
        sinon valeur brute).
        """
        return {
            "phase": _phase_value(self.phase),
            "n_findings": len(self.findings),
            "by_severity": self.count_by_severity(),
            "by_theme": self.count_by_theme(),
            "by_error_type": self.count_by_error_type(),
            "conformity_rate": round(self.conformity_rate(), 3),
            "model": self.snapshot.summary(),
        }


__all__ = ["AuditResult"]
