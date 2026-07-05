"""Garde de pureté : bim-audit-engine ne dépend que de bim-core (+ stdlib)."""

from __future__ import annotations

import sys


def test_no_audit_bim_or_network_on_import():
    for mod in list(sys.modules):
        if mod == "bim_audit_engine" or mod.startswith("bim_audit_engine."):
            del sys.modules[mod]

    import bim_audit_engine  # noqa: F401

    loaded = set(sys.modules)
    assert not any(m == "audit_bim" or m.startswith("audit_bim.") for m in loaded)
    assert "requests" not in loaded
    assert "bimdata_read" not in loaded


def test_public_surface():
    import bim_audit_engine as e

    assert set(e.__all__) == {"Rule", "run_audit", "AuditResult"}
