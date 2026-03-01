# ==============================================================================
# KatilimALM - (c) 2024-2026 Salih Say
# GitHub: github.com/SalihSay
# Bu yazilim telif haklari ile korunmaktadir.
# Izinsiz kopyalanmasi, dagitilmasi veya degistirilmesi yasaktir.
# ==============================================================================
"""
KatılımALM — Senaryo Motoru
Stres senaryolarını tanımlama, kaydetme ve yönetme.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import json
from typing import List, Optional
from models import StressScenario
import config


def create_scenario(
    name: str,
    fx_shock: float = 0.0,
    rate_shock_bp: int = 0,
    deposit_runoff: float = 0.0,
    credit_loss: float = 0.0,
    description: str = "",
) -> StressScenario:
    """Yeni stres senaryosu oluşturur."""
    return StressScenario(
        name=name,
        fx_shock=fx_shock,
        rate_shock_bp=rate_shock_bp,
        deposit_runoff=deposit_runoff,
        credit_loss=credit_loss,
        description=description,
    )


def load_preset_scenarios() -> List[StressScenario]:
    """Config'den önceden tanımlı senaryoları yükler."""
    scenarios = []
    for name, params in config.STRESS_SCENARIOS.items():
        scenarios.append(StressScenario(
            name=name,
            fx_shock=params["fx_shock"],
            rate_shock_bp=params["rate_shock_bp"],
            deposit_runoff=params["deposit_runoff"],
            credit_loss=params["credit_loss"],
            description=params.get("description", ""),
        ))
    return scenarios


def save_custom_scenario(scenario: StressScenario, path: str = None):
    """Özel senaryoyu JSON olarak kaydeder."""
    if path is None:
        path = os.path.join(
            os.path.dirname(__file__), '..', 'data', 'custom_scenarios.json'
        )
    
    existing = load_custom_scenarios(path)
    
    scenario_dict = {
        "name": scenario.name,
        "fx_shock": scenario.fx_shock,
        "rate_shock_bp": scenario.rate_shock_bp,
        "deposit_runoff": scenario.deposit_runoff,
        "credit_loss": scenario.credit_loss,
        "description": scenario.description,
    }
    
    # Aynı isimde varsa güncelle
    updated = False
    for i, s in enumerate(existing):
        if s["name"] == scenario.name:
            existing[i] = scenario_dict
            updated = True
            break
    
    if not updated:
        existing.append(scenario_dict)
    
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(existing, f, ensure_ascii=False, indent=2)


def load_custom_scenarios(path: str = None) -> list:
    """Kaydedilmiş özel senaryoları yükler."""
    if path is None:
        path = os.path.join(
            os.path.dirname(__file__), '..', 'data', 'custom_scenarios.json'
        )
    
    if not os.path.exists(path):
        return []
    
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    return data


def get_all_scenarios() -> List[StressScenario]:
    """Tüm senaryoları (öntanımlı + özel) döndürür."""
    all_scenarios = load_preset_scenarios()
    
    custom = load_custom_scenarios()
    for s in custom:
        all_scenarios.append(StressScenario(
            name=s["name"],
            fx_shock=s["fx_shock"],
            rate_shock_bp=s["rate_shock_bp"],
            deposit_runoff=s["deposit_runoff"],
            credit_loss=s["credit_loss"],
            description=s.get("description", ""),
        ))
    
    return all_scenarios
