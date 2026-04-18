""" 
rubric.py 
--------- 
Rubric definition and validation. 
The rubric is the only thing that changes between use cases. Everything else — the judge, the evaluator, the analysis — stays the same. 
A rubric defines: 
- Which dimensions to evaluate 
- What each dimension means in this domain 
- What thresholds trigger a launch pass/fail 
- How dimensions are weighted in the composite score 
""" 
from __future__ import annotations 
from dataclasses import dataclass, field 
from pathlib import Path 
from typing import Literal 
import yaml 
@dataclass 
class Rubric: 
 """ 
 Rubric configuration for a use case. 
 Parameters 
 ---------- 
 use_case : str 
 Human-readable name of the use case. 
 domain_risk_level : str 
 Risk level of the domain. Affects default thresholds.  dimensions : dict 
 Per-dimension configuration. Each dimension has:  - weight: float (how much it contributes to composite score)  - launch_threshold: float (minimum acceptable mean score)  - description: str (what this dimension means in this domain)  """ 
 use_case: str 
 domain_risk_level: Literal["low", "medium", "high"]
 dimensions: dict[str, dict] 
 # Default dimension configs by risk level 
 # Higher risk = higher thresholds, especially for grounding and risk_calibration  DEFAULTS_BY_RISK = { 
 "low": { 
 "accuracy": {"weight": 1.0, "launch_threshold": 3.8},  "completeness": {"weight": 1.0, "launch_threshold": 3.8},  "grounding": {"weight": 1.0, "launch_threshold": 3.8},  "risk_calibration": {"weight": 1.0, "launch_threshold": 3.5},  "clarity": {"weight": 0.8, "launch_threshold": 3.5},  }, 
 "medium": { 
 "accuracy": {"weight": 1.0, "launch_threshold": 4.0},  "completeness": {"weight": 1.0, "launch_threshold": 4.0},  "grounding": {"weight": 1.2, "launch_threshold": 4.0},  "risk_calibration": {"weight": 1.2, "launch_threshold": 4.0},  "clarity": {"weight": 0.8, "launch_threshold": 3.8},  }, 
 "high": { 
 "accuracy": {"weight": 1.0, "launch_threshold": 4.0},  "completeness": {"weight": 1.0, "launch_threshold": 4.0},  "grounding": {"weight": 1.3, "launch_threshold": 4.2},  "risk_calibration": {"weight": 1.3, "launch_threshold": 4.2},  "clarity": {"weight": 0.8, "launch_threshold": 3.8},  }, 
 } 
 def __post_init__(self): 
 """Apply default configs for any dimension not explicitly configured."""  defaults = self.DEFAULTS_BY_RISK.get(self.domain_risk_level, {})  for dim, default_config in defaults.items(): 
 if dim not in self.dimensions: 
 self.dimensions[dim] = default_config 
 else: 
 # Fill in any missing keys from defaults 
 for key, val in default_config.items(): 
 self.dimensions[dim].setdefault(key, val) 
 @classmethod 
 def from_yaml(cls, path: str) -> "Rubric": 
 """Load rubric from a YAML config file.""" 
 with open(path) as f: 
 config = yaml.safe_load(f) 
 return cls( 
 use_case=config["use_case"],
 domain_risk_level=config["domain_risk_level"], 
 dimensions=config.get("dimensions", {}), 
 ) 
 @classmethod 
 def from_risk_level( 
 cls, 
 use_case: str, 
 domain_risk_level: Literal["low", "medium", "high"],  ) -> "Rubric": 
 """ 
 Create a rubric using default thresholds for a given risk level.   
 Useful for quick setup when domain-specific tuning isn't needed yet.  """ 
 return cls( 
 use_case=use_case, 
 domain_risk_level=domain_risk_level, 
 dimensions={}, # Will be populated from defaults in __post_init__  ) 
 def weighted_composite(self, scores: dict[str, float]) -> float:  """Compute the weighted composite score across dimensions."""  total_weight = 0.0 
 weighted_sum = 0.0 
 for dim, score in scores.items(): 
 weight = self.dimensions.get(dim, {}).get("weight", 1.0)  weighted_sum += score * weight 
 total_weight += weight 
 return weighted_sum / total_weight if total_weight > 0 else 0.0 
 def validate(self) -> list[str]: 
 """Return list of validation warnings for this rubric config."""  warnings = [] 
 required_dims = ["accuracy", "completeness", "grounding",  "risk_calibration", "clarity"] 
 for dim in required_dims: 
 if dim not in self.dimensions: 
 warnings.append(f"Missing dimension: {dim}")  else: 
 cfg = self.dimensions[dim] 
 if "launch_threshold" not in cfg: 
 warnings.append(f"Missing launch_threshold for: {dim}")  elif not (1.0 <= cfg["launch_threshold"] <= 5.0):  warnings.append( 
 f"launch_threshold for {dim} out of range [1, 5]: "
 f"{cfg['launch_threshold']}" 
 ) 
 if self.domain_risk_level not in ("low", "medium", "high"):  warnings.append(f"Invalid domain_risk_level: {self.domain_risk_level}") 
 return warnings 
 def summary(self) -> str: 
 lines = [ 
 f"Rubric: {self.use_case}", 
 f"Risk level: {self.domain_risk_level}", 
 f"\n{'Dimension':<22} {'Weight':>8} {'Threshold':>10}",  "-" * 42, 
 ] 
 for dim, cfg in self.dimensions.items(): 
 lines.append( 
 f"{dim:<22} {cfg.get('weight', 1.0):>8.1f} " 
 f"{cfg.get('launch_threshold', '?'):>10}" 
 ) 
 return "\n".join(lines)
