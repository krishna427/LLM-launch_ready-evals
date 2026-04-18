""" 
evaluator.py 
------------ 
Core evaluation pipeline for LLM launch readiness assessment. 
Designed to be use-case agnostic. The rubric and dataset are injected at runtime — the evaluation logic stays the same regardless of domain. 
This separation is intentional: measurement methodology should not be rebuilt for every new LLM feature. The domain-specific part (what questions to ask, what thresholds to set) lives in the use case config. The statistical machinery lives here. 
""" 
from __future__ import annotations 
import json 
from dataclasses import dataclass, field 
from pathlib import Path 
from typing import Callable, Optional 
import numpy as np 
import pandas as pd 
from core.rubric import Rubric 
from core.judge import LLMJudge 
DIMENSIONS = ["accuracy", "completeness", "grounding", "risk_calibration", "clarity"] 
@dataclass 
class EvalResult: 
 """ 
 Full evaluation result for a single response. 
  
 Carries both automated and human scores when available, 
 plus metadata needed for gap analysis. 
 """ 
 item_id: str 
 question: str 
 category: str 
 difficulty: str 
 domain_risk: str
 auto_scores: dict[str, float] # LLM judge scores 
 human_scores: dict[str, float] # Human / simulated human scores  auto_reasoning: str 
 critical_gap: str # Most important thing the response missed  disagreement_flag: bool 
 disagreement_dimensions: list[str] 
 @property 
 def auto_composite(self) -> float: 
 return float(np.mean(list(self.auto_scores.values()))) 
 @property 
 def human_composite(self) -> float: 
 return float(np.mean(list(self.human_scores.values()))) 
 @property 
 def max_disagreement(self) -> float: 
 return max( 
 abs(self.auto_scores.get(d, 0) - self.human_scores.get(d, 0))  for d in DIMENSIONS 
 if d in self.auto_scores and d in self.human_scores  ) 
@dataclass 
class EvalReport: 
 """ 
 Aggregated evaluation report across all items. 
  
 The primary output of the pipeline. Contains per-dimension statistics,  launch verdict, and the gap analysis between automated and human eval.  """ 
 rubric: Rubric 
 results: list[EvalResult] 
 n_items: int 
 def _df(self) -> pd.DataFrame: 
 """Flatten results to DataFrame for analysis.""" 
 rows = [] 
 for r in self.results: 
 base = { 
 "id": r.item_id, 
 "category": r.category, 
 "difficulty": r.difficulty, 
 "domain_risk": r.domain_risk, 
 "disagreement_flag": r.disagreement_flag, 
 "auto_composite": r.auto_composite,
 "human_composite": r.human_composite, 
 } 
 for d in DIMENSIONS: 
 base[f"auto_{d}"] = r.auto_scores.get(d) 
 base[f"human_{d}"] = r.human_scores.get(d) 
 rows.append(base) 
 return pd.DataFrame(rows) 
 def launch_verdict(self) -> dict: 
 """ 
 Compute launch readiness verdict against rubric thresholds. 
  
 Uses human scores where available, falls back to automated scores.  All configured dimensions must clear their thresholds for a PASS.  """ 
 df = self._df() 
 verdict = {} 
 all_pass = True 
 print(f"\n{'='*60}") 
 print("LAUNCH READINESS VERDICT") 
 print(f"{'='*60}") 
 print(f"{'Dimension':<22} {'Score':>8} {'Threshold':>10} {'Status':>8}")  print(f"{'-'*52}") 
 for dim, config in self.rubric.dimensions.items(): 
 col = f"human_{dim}" if f"human_{dim}" in df.columns else f"auto_{dim}"  mean_score = df[col].mean() 
 threshold = config["launch_threshold"] 
 passed = mean_score >= threshold 
 if not passed: 
 all_pass = False 
 status = " PASS" if passed else " FAIL" 
 print(f"{dim:<22} {mean_score:>8.2f} {threshold:>10.1f} {status:>8}")  verdict[dim] = {"score": mean_score, "threshold": threshold, "passed": passed} 
 print(f"\n{'='*60}") 
 overall = " CONDITIONALLY READY" if all_pass else " NOT READY FOR LAUNCH"  print(f"Overall: {overall}") 
 print(f"{'='*60}\n") 
 verdict["overall_pass"] = all_pass 
 return verdict 
 def gap_analysis(self) -> pd.DataFrame:
 """ 
 Where does automated evaluation diverge from human evaluation?   
 This is the most analytically valuable output — it tells you  which dimensions of automated eval to trust and which to verify.  """ 
 df = self._df() 
 rows = [] 
 for dim in DIMENSIONS: 
 if f"auto_{dim}" not in df.columns: 
 continue 
 auto_mean = df[f"auto_{dim}"].mean() 
 human_mean = df[f"human_{dim}"].mean() 
 bias = auto_mean - human_mean 
 corr = df[f"auto_{dim}"].corr(df[f"human_{dim}"]) 
 disagreement_rate = ( 
 (df[f"auto_{dim}"] - df[f"human_{dim}"]).abs() >= 1  ).mean() 
 rows.append({ 
 "dimension": dim, 
 "auto_mean": round(auto_mean, 3), 
 "human_mean": round(human_mean, 3), 
 "bias": round(bias, 3), 
 "correlation": round(corr, 3), 
 "disagreement_rate": round(disagreement_rate, 3), 
 "trust_automated": "yes" if abs(bias) < 0.2 and corr > 0.7 else "no",  }) 
 gap_df = pd.DataFrame(rows).set_index("dimension") 
 print("\n=== Automated Evaluation Trust Analysis ===") 
 print(gap_df.to_string()) 
 return gap_df 
 def failure_report(self) -> pd.DataFrame: 
 """ 
 Surface responses with quality issues worth investigating. 
  
 Flags any response where human score < 4.0 on any dimension,  sorted by severity of the worst failure. 
 """ 
 df = self._df() 
 human_cols = [f"human_{d}" for d in DIMENSIONS if f"human_{d}" in df.columns]  df["min_human_score"] = df[human_cols].min(axis=1) 
 df["weakest_dimension"] = df[human_cols].idxmin(axis=1).str.replace("human_", "")  failures = df[df["min_human_score"] < 4.0].sort_values("min_human_score")
 print(f"\n=== Failure Report: {len(failures)}/{self.n_items} responses with quality  if len(failures) > 0: 
 print(failures[["id", "category", "difficulty", "weakest_dimension", "min_human_ return failures 
 def disagreement_cases(self) -> list[EvalResult]: 
 """Return cases where human and automated evaluation notably diverged."""  return [r for r in self.results if r.disagreement_flag] 
class EvalPipeline: 
 """ 
 Orchestrates the full evaluation run. 
  
 Designed for reuse across use cases. The rubric and dataset paths 
 are the only things that change between domains. 
  
 Parameters 
 ---------- 
 rubric : Rubric 
 Loaded rubric configuration for the use case. 
 judge_model : str 
 Model to use as the automated judge. 
 human_scores_path : str, optional 
 Path to human annotation file. If not provided, only automated  scores are computed (gap analysis is skipped). 
 """ 
 def __init__( 
 self, 
 rubric: Rubric, 
 judge_model: str = "gpt-4o", 
 human_scores_path: Optional[str] = None, 
 ): 
 self.rubric = rubric 
 self.judge = LLMJudge(model=judge_model, rubric=rubric) 
 self.human_scores_path = human_scores_path 
 def run( 
 self, 
 dataset_path: str, 
 model_responses_path: str, 
 ) -> EvalReport: 
 """ 
 Run evaluation on a dataset + model responses.
  
 Parameters 
 ---------- 
 dataset_path : str 
 Path to the dataset JSON (questions + reference answers).  model_responses_path : str 
 Path to model responses JSON. Expected format: 
 [{"id": "...", "response": "..."}] 
 """ 
 with open(dataset_path) as f: 
 dataset = {item["id"]: item for item in json.load(f)} 
 with open(model_responses_path) as f: 
 responses = {item["id"]: item["response"] for item in json.load(f)} 
 human_scores = {} 
 if self.human_scores_path: 
 with open(self.human_scores_path) as f: 
 human_scores = {item["id"]: item for item in json.load(f)} 
 results = [] 
 for item_id, item in dataset.items(): 
 if item_id not in responses: 
 continue 
 auto_result = self.judge.score( 
 question=item["question"], 
 reference_answer=item["reference_answer"], 
 model_response=responses[item_id], 
 ) 
 human = human_scores.get(item_id, {}) 
 h_scores = human.get("scores", auto_result["scores"]) # Fall back to auto 
 # Detect disagreement: any dimension differs by >= 1 point  disagreement_dims = [ 
 d for d in DIMENSIONS 
 if abs(auto_result["scores"].get(d, 0) - h_scores.get(d, 0)) >= 1  ] 
 results.append(EvalResult( 
 item_id=item_id, 
 question=item["question"], 
 category=item.get("category", "unknown"), 
 difficulty=item.get("difficulty", "unknown"), 
 domain_risk=item.get("domain_risk", "medium"), 
 auto_scores=auto_result["scores"],
 human_scores=h_scores, 
 auto_reasoning=auto_result.get("reasoning", ""),  critical_gap=auto_result.get("critical_gap", "none"),  disagreement_flag=len(disagreement_dims) > 0,  disagreement_dimensions=disagreement_dims,  )) 
 return EvalReport( 
 rubric=self.rubric, 
 results=results, 
 n_items=len(results), 
 )
