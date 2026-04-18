
llm-eval-toolkit
An open framework for evaluating the launch readiness of LLM assistants in high-risk domains.
This project is independently created using publicly available information and self-generated data. It does not reflect the methods, systems, data, or opinions of any current or former employer.
Why This Exists
Shipping an LLM assistant into a domain where wrong answers have real consequences requires more than a vibe check.
The standard approaches fail in predictable ways:
	•	Manual review doesn’t scale. You can’t read 10,000 responses before every release.
	•	LLM-as-judge is biased. Automated evaluators systematically overrate fluency and underrate what’s missing.
	•	Aggregate scores hide the tail. A mean score of 4.3/5.0 can mask a dangerous distribution of failures.
This toolkit makes those problems tractable. Swap the dataset and rubric — the infrastructure stays the same.
The Five Dimensions



|Dimension       |What It Captures                                                |
|----------------|----------------------------------------------------------------|
|Accuracy        |Is the information factually correct?                           |
|Completeness    |Does it cover what the user actually needs?                     |
|Grounding       |Are claims supported, or does omission create false impressions?|
|Risk Calibration|Is uncertainty appropriately surfaced?                          |
|Clarity         |Is it understandable to the intended audience?                  |

The Core Finding
The most important thing this framework surfaces: the gap between automated and human evaluation.



|Dimension       |Auto|Human|Bias |
|----------------|----|-----|-----|
|accuracy        |4.87|4.67 |+0.20|
|completeness    |4.60|4.27 |+0.33|
|grounding       |4.87|4.53 |+0.34|
|risk_calibration|4.53|4.20 |+0.33|
|clarity         |4.93|4.87 |+0.07|

Clarity: trust automated evaluation. Everything else: verify.
Quick Start

from core.evaluator import EvalPipeline
from core.rubric import Rubric

rubric = Rubric.from_yaml("use_cases/personal_finance_qa/rubric.yaml")
pipeline = EvalPipeline(rubric=rubric, judge_model="gpt-4o")

results = pipeline.run(
    dataset_path="use_cases/personal_finance_qa/dataset.json",
    model_responses_path="your_model_outputs.json",
)

results.launch_verdict()
results.gap_analysis()
results.failure_report()


Repository Structure

llm-eval-toolkit/
├── README.md
├── core/
│   ├── evaluator.py
│   ├── judge.py
│   └── rubric.py
├── use_cases/
│   ├── personal_finance_qa/
│   │   ├── dataset.json
│   │   └── rubric.yaml
│   └── template/
├── prompts/
│   └── judge_prompt.txt
├── notebooks/
│   └── eval_analysis.py
└── results/


Adding a New Use Case
	1.	Copy use_cases/template/ to use_cases/your_use_case/
	2.	Write your dataset — 15 examples minimum
	3.	Configure thresholds in rubric.yaml
	4.	Run notebooks/eval_analysis.py
The framework is domain-agnostic and designed to generalize to any high-risk informational assistant.
Limitations
	•	Reference implementation uses 15 examples — enough to surface patterns, not make statistical claims
	•	Human scores are simulated based on domain knowledge, not collected from real annotators
	•	No latency or cost analysis included
License
MIT
This project is independently created using publicly available information and self-generated data. It does not reflect the methods, systems, data, or opinions of any current or former employer.