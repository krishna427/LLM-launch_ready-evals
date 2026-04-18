llm-eval-toolkit 
An open framework for evaluating the launch readiness of LLM assistants in high-risk domains. 
This project is independently created using publicly available information and self generated data. It does not reflect the methods, systems, data, or opinions of any current or former employer. 
Why This Exists 
Shipping an LLM assistant into a domain where wrong answers have real consequences — health, money, law, safety — requires more than a vibe check. 
The standard approaches fail in predictable ways: 
Manual review doesn’t scale. You can’t read 10,000 responses before every release. 
LLM-as-judge is biased. Automated evaluators systematically overrate fluency and underrate what’s missing. 
Aggregate scores hide the tail. A mean score of 4.3/5.0 can mask a dangerous distribution of edge case failures. 
This toolkit makes those problems tractable. It’s designed to be pointed at any LLM assistant use case with minimal configuration — swap the dataset and rubric, the infrastructure stays the same. 
Core Concepts 
The Five Dimensions 
Every response is evaluated on five dimensions, chosen for generalizability across high-risk domains:
Dimension 
What It Captures






Accuracy 
Is the information factually correct?
Completeness 
Does it cover what the user actually needs to know?
Grounding 
Are claims supported, or does the model assert without basis?
Risk Calibration 
Does it appropriately flag uncertainty and limits?
Clarity 
Is it understandable to the intended audience?



These are intentionally generic. The rubric for each dimension is configured per use case — what “complete” means for a medical information assistant differs from what it means for a coding assistant. 
The Evaluation Gap 
The most important finding this framework is designed to surface: the gap between automated and human evaluation. 
LLM judges are reliable for some things (factual errors, clarity, formatting) and systematically unreliable for others (errors of omission, false impressions created by technically accurate but incomplete answers, risk calibration). 
Knowing where to trust automated evaluation and where to require human review is what separates a credible launch process from a rubber stamp. 
Launch Readiness vs. Quality Score 
A quality score tells you how good responses are on average. Launch readiness tells you whether the distribution of responses is acceptable — including the tail. 
This toolkit computes both, and flags cases where average quality masks unacceptable tail risk. 
Repository Structure 
llm-eval-toolkit/ 
├── README.md ← You are here 
├── core/ 
│ ├── evaluator.py ← Core evaluation loop 
│ ├── judge.py ← LLM-as-judge engine 
│ └── rubric.py ← Rubric interface and validation ├── use_cases/
│ ├── personal_finance_qa/ ← Reference implementation │ │ ├── dataset.json ← Self-generated Q&A with annotations │ │ ├── rubric.yaml ← Domain-specific rubric config │ │ └── README.md ← Use case documentation │ └── template/ ← Blank template for new use cases │ ├── dataset_template.json 
│ ├── rubric_template.yaml 
│ └── README.md 
├── prompts/ 
│ └── judge_prompt.txt ← Generic LLM judge prompt ├── notebooks/ 
│ └── eval_analysis.py ← Analysis + visualizations └── results/ ← Output artifacts 
Using the Framework 
Step 1: Define your rubric 
# use_cases/your_use_case/rubric.yaml 
use_case: "Your assistant name" 
domain_risk_level: high # low / medium / high 
dimensions: 
 accuracy: 
 weight: 1.0 
 launch_threshold: 4.0 
 description: "Factual correctness of the response" 
 completeness: 
 weight: 1.0 
 launch_threshold: 4.0 
 description: "Whether the response covers what the user needs" 
 grounding: 
 weight: 1.2 # Upweighted for high-risk domains  launch_threshold: 4.2 
 description: "Claims are supported or appropriately hedged" 
 risk_calibration: 
 weight: 1.2 
 launch_threshold: 4.2 
 description: "Uncertainty and limits are appropriately surfaced"
 clarity: 
 weight: 0.8 
 launch_threshold: 3.8 
 description: "Understandable to the intended audience" 
Step 2: Build your dataset 
{ 
 "id": "UC_001", 
 "category": "your_category", 
 "difficulty": "medium", 
 "domain_risk": "high", 
 "question": "Your question here", 
 "reference_answer": "What a correct, complete answer looks like",  "known_failure_modes": ["list", "of", "expected", "gaps"] 
} 
Step 3: Run evaluation 
from core.evaluator import EvalPipeline 
from core.rubric import Rubric 
rubric = Rubric.from_yaml("use_cases/your_use_case/rubric.yaml") pipeline = EvalPipeline(rubric=rubric, judge_model="gpt-4o") 
results = pipeline.run( 
 dataset_path="use_cases/your_use_case/dataset.json", 
 model_responses_path="your_model_outputs.json", 
) 
results.launch_verdict() # Pass / Fail with dimension breakdown results.failure_report() # What broke and why 
results.gap_analysis() # Where automated eval diverges from human 
Reference Implementation: Personal Finance Q&A 
The use_cases/personal_finance_qa/ directory contains a complete worked example evaluating an LLM assistant answering general personal finance education questions. 
Domain: General financial literacy (budgeting, debt, savings concepts) Risk level: High — incorrect information can affect real financial decisions Dataset: 15 self-generated
questions with reference answers and dual scoring (automated + simulated human review) 
Key findings from this implementation 
1. Grounding failures are the primary risk vector 
The most common failure mode wasn’t factually wrong answers — it was answers that created false impressions through omission. Technically accurate responses that left out the critical nuance a user would need to make a safe decision. 
The automated judge consistently missed these. Human review caught them. This finding drives the framework’s recommendation to use automated evaluation for accuracy and clarity, and human review for grounding and risk calibration. 
2. LLM judge systematic bias by dimension 
Dimension LLM Mean Human Mean Bias 
accuracy 4.87 4.67 +0.20 
completeness 4.60 4.27 +0.33  
grounding 4.87 4.53 +0.34  
risk_calibration 4.53 4.20 +0.33  
clarity 4.93 4.87 +0.07 
Clarity: automated evaluation is reliable. Everything else: trust but verify. 3. Difficulty is a stronger predictor of failure than category 
Hard questions showed a 40% human/LLM disagreement rate. Easy questions: 0%. Implication: tiered evaluation strategy — automated for definitional queries, human review for decision-support queries. 
What Good Launch Readiness Looks Like 
A launch readiness process built on this framework has three layers: 
Layer 1 — Automated sweep (all queries) Run every response through the LLM judge. Catches factual errors, clarity issues, formatting problems. Fast and cheap. 
Layer 2 — Human spot-check (high-risk queries) Route queries above a risk threshold to human reviewers. Focus on grounding and risk calibration — the dimensions where automated eval is weakest. 
Layer 3 — Tail analysis (flagged cases) Review the bottom 5% of automated scores in detail. This is where dangerous responses hide.
Launch when all three layers clear their thresholds — not when the mean score looks good. 
Limitations 
Dataset size: The reference implementation uses 15 examples — enough to surface patterns, not to make statistical claims. Production evaluation needs 500+. 
Single model evaluated: This framework compares evaluation methods. Adding a second model creates natural A/B comparison. 
Simulated human scores: Human scores in the reference implementation are simulated based on domain knowledge, not collected from real annotators. 
No latency or cost analysis: Production launch readiness also includes p99 latency and cost per query — not in scope here. 
Extending the Framework 
To add a new use case: 
1. Copy use_cases/template/ to use_cases/your_use_case/ 
2. Write your dataset (minimum 15 examples; 50+ recommended) 
3. Configure your rubric weights and thresholds 
4. Run the pipeline and review the gap analysis 
The framework is intentionally domain-agnostic. It has been tested on personal finance Q&A and is designed to generalize to any high-risk informational assistant. 
Contributing 
PRs welcome, especially for: 
New use case implementations 
Additional judge prompt variants 
Visualization improvements 
Statistical rigor improvements (bootstrap CIs, inter-rater reliability)
License 
MIT 
This project is independently created using publicly available information and self generated data. It does not reflect the methods, systems, data, or opinions of any current or former employer.
