# llm-eval-toolkit

**An open framework for evaluating the launch readiness of LLM assistants in high-risk domains.**

> *This project is independently created using publicly available information and self-generated data. It does not reflect the methods, systems, data, or opinions of any current or former employer.*

---

## Why This Exists

Shipping an LLM assistant into a domain where wrong answers have real consequences — health, money, law, safety — requires more than a vibe check.

The standard approaches fail in predictable ways:

- **Manual review doesn't scale.** You can't read 10,000 responses before every release.
- **LLM-as-judge is biased.** Automated evaluators systematically overrate fluency and underrate what's missing.
- **Aggregate scores hide the tail.** A mean score of 4.3/5.0 can mask a dangerous distribution of edge case failures.

This toolkit makes those problems tractable. Swap the dataset and rubric — the infrastructure stays the same.

---

## The Five Dimensions

| Dimension | What It Captures |
|-----------|-----------------|
| **Accuracy** | Is the information factually correct? |
| **Completeness** | Does it cover what the user actually needs? |
| **Grounding** | Are claims supported, or does omission create false impressions? |
| **Risk Calibration** | Is uncertainty appropriately surfaced? |
| **Clarity** | Is it understandable to the intended audience? |

---

## The Core Finding

The most important thing this framework surfaces: **the gap between automated and human evaluation.**

LLM judges are reliable for some things (factual errors, clarity) and systematically unreliable for others (errors of omission, false impressions created by technically accurate but incomplete answers).


Clarity: trust automated evaluation. Everything else: verify.

---

## Quick Start

```python
from core.evaluator import EvalPipeline
from core.rubric import Rubric

rubric = Rubric.from_yaml("use_cases/personal_finance_qa/rubric.yaml")

pipeline = EvalPipeline(rubric=rubric, judge_model="gpt-4o")

results = pipeline.run(
    dataset_path="use_cases/personal_finance_qa/dataset.json",
    model_responses_path="your_model_outputs.json",
)

results.launch_verdict()    # Pass / Fail per dimension
results.gap_analysis()      # Where auto eval diverges from human
results.failure_report()    # What broke and why


llm-eval-toolkit/
├── README.md
├── core/
│   ├── evaluator.py         ← Core evaluation loop
│   ├── judge.py             ← LLM-as-judge engine
│   └── rubric.py            ← Rubric interface
├── use_cases/
│   ├── personal_finance_qa/ ← Reference implementation
│   │   ├── dataset.json
│   │   └── rubric.yaml
│   └── template/            ← Blank template for new use cases
├── prompts/
│   └── judge_prompt.txt     ← Generic judge prompt
├── notebooks/
│   └── eval_analysis.py     ← Analysis + visualizations
└── results/


---

After pasting:

1. Click **Preview** tab — you should see headers, a table, and code blocks rendering cleanly
2. If it looks good → scroll down → **Commit changes**
3. Go back to your repo homepage and the README will render correctly

Let me know what you see in Preview.​​​​​​​​​​​​​​​​

