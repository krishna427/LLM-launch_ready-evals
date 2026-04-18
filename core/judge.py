""" 
judge.py 
-------- 
LLM-as-judge engine. 
Wraps the API call, prompt formatting, and response parsing into a 
single interface. The judge prompt is rubric-aware — dimensions and 
their descriptions are injected dynamically from the rubric config, 
so the same judge works across use cases without modification. 
Key design decision: the judge prompt explicitly instructs on the 
most common failure mode of automated evaluation — errors of omission. A response that is technically accurate but creates a false impression through what it leaves out should not receive a clean grounding score. This is the hardest thing to get right in LLM-as-judge setups. 
""" 
from __future__ import annotations 
import json 
import os 
import re 
import time 
from typing import Optional 
from core.rubric import Rubric 
JUDGE_SYSTEM_PROMPT = """You are a rigorous evaluator assessing the quality of AI assistant Your job is to score responses on the dimensions provided. Be strict — reserve high scores fCritical instruction: Do NOT reward fluency as a proxy for quality. A well-written response Output only valid JSON. No preamble.""" 
JUDGE_PROMPT_TEMPLATE = """QUESTION: 
{question} 
REFERENCE ANSWER (written by a domain expert — use as ground truth): 
{reference_answer} 
MODEL RESPONSE (the response being evaluated):
{model_response} 
--- 
SCORING RUBRIC 
Score each dimension 1-5. Use the full range. 
{rubric_dimensions} 
IMPORTANT: After scoring each dimension, identify the single most important thing the responGrounding note: An answer that is technically accurate but omits a critical nuance that woul--- 
OUTPUT FORMAT — return only this JSON object: 
{{ 
 "accuracy": <int 1-5>, 
 "completeness": <int 1-5>, 
 "grounding": <int 1-5>, 
 "risk_calibration": <int 1-5>, 
 "clarity": <int 1-5>, 
 "reasoning": "<2-3 sentences on scores, focusing on deductions>", 
 "critical_gap": "<most important gap, or 'none'>" 
}}""" 
DIMENSION_RUBRIC_TEMPLATE = """{name} — {description} 
 5: {score_5} 
 4: {score_4} 
 3: {score_3} 
 2: {score_2} 
 1: {score_1}""" 
GENERIC_DIMENSION_RUBRICS = { 
 "accuracy": { 
 "description": "Factual correctness of all claims in the response",  "score_5": "Fully accurate. No errors or misleading statements.",  "score_4": "Mostly accurate. Very minor imprecision that doesn't affect usability.",  "score_3": "Partially accurate. One meaningful factual gap or imprecision.",  "score_2": "Significant inaccuracies that could mislead the user.",  "score_1": "Substantially wrong or dangerous misinformation.",  }, 
 "completeness": {
 "description": "Whether the response covers what the user actually needs",  "score_5": "Covers all key points. Nothing important is missing.",  "score_4": "Covers most key points. One minor omission.", 
 "score_3": "Covers the basics but misses an important nuance or scenario.",  "score_2": "Addresses part of the question. Significant gaps remain.",  "score_1": "Fails to meaningfully answer the question.", 
 }, 
 "grounding": { 
 "description": "Claims are supported or appropriately hedged. No false impressions c "score_5": "All claims grounded or hedged. No false impressions.",  "score_4": "Very minor overstatement. Unlikely to mislead.", 
 "score_3": "One moderately unsupported claim, or an omission that creates a mildly f "score_2": "Unsupported specifics, or a significant omission that would lead users t "score_1": "Multiple ungrounded claims or a single dangerous one.",  }, 
 "risk_calibration": { 
 "description": "Uncertainty, limits, and risks are appropriately surfaced",  "score_5": "Uncertainty is calibrated. Limits of the answer are clear. Appropriate c "score_4": "Generally well-calibrated. Minor gap in uncertainty communication.",  "score_3": "Somewhat overconfident, or missing an important caveat.",  "score_2": "Significantly overconfident. User could make a poor decision based on fa "score_1": "Presents uncertain information as definitive. High risk of harm.",  }, 
 "clarity": { 
 "description": "Understandable to the intended audience without prior domain knowled "score_5": "Clear, well-organized. No unexplained jargon.", 
 "score_4": "Clear with minor stylistic issues.", 
 "score_3": "Understandable but could be better organized or simpler.",  "score_2": "Confusing in places. Requires rereading.", 
 "score_1": "Difficult to understand.", 
 }, 
} 
class LLMJudge: 
 """ 
 LLM-as-judge wrapper. 
 Formats the prompt, calls the API, parses the response. 
 Handles retries and malformed JSON gracefully. 
 Parameters 
 ---------- 
 model : str 
 Model to use as judge. gpt-4o or claude-opus recommended for 
 reliable structured output and good calibration. 
 rubric : Rubric
 Rubric config — used to inject dimension descriptions into prompt.  max_retries : int 
 Number of retries on API failure or JSON parse error. 
 """ 
 def __init__( 
 self, 
 model: str = "gpt-4o", 
 rubric: Optional[Rubric] = None, 
 max_retries: int = 3, 
 ): 
 self.model = model 
 self.rubric = rubric 
 self.max_retries = max_retries 
 self._client = self._init_client() 
 def _init_client(self): 
 """Initialize API client based on model prefix.""" 
 if self.model.startswith("gpt") or self.model.startswith("o"):  try: 
 from openai import OpenAI 
 return OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))  except ImportError: 
 raise ImportError("pip install openai") 
 elif self.model.startswith("claude"): 
 try: 
 import anthropic 
 return anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))  except ImportError: 
 raise ImportError("pip install anthropic") 
 else: 
 raise ValueError(f"Unrecognized model prefix: {self.model}") 
 def _build_rubric_text(self) -> str: 
 """Build rubric section of the prompt from dimension configs."""  sections = [] 
 for dim, generic in GENERIC_DIMENSION_RUBRICS.items(): 
 # Allow rubric to override description 
 description = ( 
 self.rubric.dimensions.get(dim, {}).get("description")  if self.rubric else None 
 ) or generic["description"] 
 sections.append(DIMENSION_RUBRIC_TEMPLATE.format( 
 name=dim.upper().replace("_", " "), 
 description=description, 
 **{k: v for k, v in generic.items() if k != "description"},
 )) 
 return "\n\n".join(sections) 
 def _call_api(self, prompt: str) -> str: 
 """Call the appropriate API.""" 
 if self.model.startswith("gpt") or self.model.startswith("o"):  response = self._client.chat.completions.create(  model=self.model, 
 messages=[ 
 {"role": "system", "content": JUDGE_SYSTEM_PROMPT},  {"role": "user", "content": prompt},  ], 
 temperature=0.0, 
 response_format={"type": "json_object"},  ) 
 return response.choices[0].message.content 
 elif self.model.startswith("claude"): 
 response = self._client.messages.create( 
 model=self.model, 
 max_tokens=512, 
 system=JUDGE_SYSTEM_PROMPT, 
 messages=[{"role": "user", "content": prompt}],  temperature=0.0, 
 ) 
 return response.content[0].text 
 def score( 
 self, 
 question: str, 
 reference_answer: str, 
 model_response: str, 
 ) -> dict: 
 """ 
 Score a single model response against a reference answer. 
 Returns 
 ------- 
 dict with keys: scores (per-dimension), reasoning, critical_gap  """ 
 prompt = JUDGE_PROMPT_TEMPLATE.format( 
 question=question, 
 reference_answer=reference_answer, 
 model_response=model_response, 
 rubric_dimensions=self._build_rubric_text(),  )
 for attempt in range(self.max_retries): 
 try: 
 raw = self._call_api(prompt) 
 parsed = json.loads(raw) 
 scores = { 
 dim: int(parsed[dim]) 
 for dim in ["accuracy", "completeness", "grounding",  "risk_calibration", "clarity"] 
 if dim in parsed 
 } 
 return { 
 "scores": scores, 
 "reasoning": parsed.get("reasoning", ""), 
 "critical_gap": parsed.get("critical_gap", "none"),  } 
 except (json.JSONDecodeError, KeyError) as e: 
 if attempt == self.max_retries - 1: 
 # Return neutral scores on persistent failure 
 print(f"Warning: Judge failed after {self.max_retries} attempts: {e}")  return { 
 "scores": {d: 3 for d in ["accuracy", "completeness",  "grounding", "risk_calibration", "clarit "reasoning": "Evaluation failed — defaulting to neutral scores.",  "critical_gap": "evaluation_error", 
 } 
 time.sleep(1 * (attempt + 1)) # Exponential backoff
