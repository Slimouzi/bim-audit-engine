"""Cœur du moteur : ``run_audit`` (règles injectables), ``AuditResult``, tri."""

from __future__ import annotations

from enum import Enum

from bim_core.findings import ErrorType, Finding, Severity, Theme
from bim_core.model_snapshot import ModelSnapshot

from bim_audit_engine import AuditResult, run_audit


class Phase(str, Enum):
    AVP = "AVP"
    DOE = "DOE"


class FakeCatalog:
    """Catalogue factice : le moteur ne l'interprète pas, il le transporte."""

    def __init__(self, name: str = "catalog") -> None:
        self.name = name


def _snapshot() -> ModelSnapshot:
    return ModelSnapshot(
        project={"name": "P"},
        model={"name": "M.ifc"},
        elements=[
            {"uuid": "W1", "type": "IfcWall", "name": "Mur"},
            {"uuid": "D1", "type": "IfcDoor", "name": "Porte"},
        ],
    ).index()


def _finding(sev: Severity, *, theme=Theme.PROPERTY_MISSING, uuid="W1", ifc="IfcWall", name="x"):
    return Finding(
        theme=theme,
        severity=sev,
        error_type=ErrorType.PROPERTY_MISSING,
        element_uuid=uuid,
        ifc_type=ifc,
        name=name,
    )


# ── Règles injectables (fonctions module-level = Rule structurel) ─────────


def _rule_high(snap, catalog, phase):
    return [_finding(Severity.HIGH, name="b")]


def _rule_low_and_critical(snap, catalog, phase):
    return [_finding(Severity.LOW, name="a"), _finding(Severity.CRITICAL, name="c")]


# ── Tests ────────────────────────────────────────────────────────────────


def test_zero_rules_gives_empty_result():
    snap = _snapshot()
    cat = FakeCatalog()
    res = run_audit(snap, cat, Phase.AVP, rules=[])
    assert isinstance(res, AuditResult)
    assert res.findings == []
    assert res.catalog is cat
    assert res.phase is Phase.AVP
    assert res.snapshot is snap


def test_multiple_rules_aggregate():
    res = run_audit(
        _snapshot(), FakeCatalog(), Phase.AVP, rules=[_rule_high, _rule_low_and_critical]
    )
    assert len(res.findings) == 3


def test_deterministic_sort_severity_first():
    res = run_audit(
        _snapshot(), FakeCatalog(), Phase.AVP, rules=[_rule_high, _rule_low_and_critical]
    )
    sevs = [f.severity for f in res.findings]
    # CRITICAL avant HIGH avant LOW, quel que soit l'ordre des règles.
    assert sevs == [Severity.CRITICAL, Severity.HIGH, Severity.LOW]


def test_sort_is_stable_regardless_of_rule_order():
    a = run_audit(_snapshot(), FakeCatalog(), Phase.AVP, rules=[_rule_high, _rule_low_and_critical])
    b = run_audit(_snapshot(), FakeCatalog(), Phase.AVP, rules=[_rule_low_and_critical, _rule_high])
    assert [f.name for f in a.findings] == [f.name for f in b.findings]


def test_rule_receives_snapshot_catalog_phase():
    seen = {}

    def _spy(snap, catalog, phase):
        seen["snap"], seen["catalog"], seen["phase"] = snap, catalog, phase
        return []

    snap, cat = _snapshot(), FakeCatalog()
    run_audit(snap, cat, Phase.DOE, rules=[_spy])
    assert seen["snap"] is snap
    assert seen["catalog"] is cat
    assert seen["phase"] is Phase.DOE


def test_phase_str_works_and_summary_tolerant():
    # Phase = str brute (pas un Enum) : summary() ne doit pas casser.
    res = run_audit(_snapshot(), FakeCatalog(), "AVP", rules=[_rule_high])
    s = res.summary()
    assert s["phase"] == "AVP"
    assert s["n_findings"] == 1


def test_phase_enum_summary_uses_value():
    res = run_audit(_snapshot(), FakeCatalog(), Phase.DOE, rules=[_rule_high])
    assert res.summary()["phase"] == "DOE"


def test_fake_catalog_passed_through_untouched():
    cat = FakeCatalog("mon-catalogue")
    res = run_audit(_snapshot(), cat, Phase.AVP, rules=[])
    assert res.catalog is cat
    assert res.catalog.name == "mon-catalogue"


def test_auditresult_stats_and_filter():
    res = run_audit(
        _snapshot(),
        FakeCatalog(),
        Phase.AVP,
        rules=[_rule_high, _rule_low_and_critical],
    )
    assert res.count_by_severity() == {"CRITICAL": 1, "HIGH": 1, "LOW": 1}
    assert res.count_by_theme()["Propriété manquante"] == 3
    assert 0.0 <= res.conformity_rate() <= 1.0
    assert len(res.filter(severity="HIGH")) == 1
