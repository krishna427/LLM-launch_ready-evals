# llm-eval-toolkit

A lightweight, general-purpose framework for evaluating the launch readiness of LLM assistants.

> *This project is independently created using publicly available information and self-generated data. It does not reflect the methods, systems, data, or opinions of any current or former employer.*

## What It Does

Takes three inputs:
- Your questions
- Your model's responses
- Your rubric

Returns structured scores, a launch verdict, and an analysis of where automated evaluation diverges from human judgment.

## The Five Dimensions

| Dimension | What It Captures |
|-----------|-----------------|
| Accuracy | Are the facts correct? |
| Completeness | Does it cover what the user needs? |
| Grounding | Are claims supported, or does omission mislead? |
| Risk Calibration | Is uncertainty appropriately surfaced? |
| Clarity | Is it understandable to the intended audience? |

## Quick Start

```python
from core.evaluator import EvalPipeline
from core.rubric import Rubric

rubric = Rubric.from_risk_level(
    use_case="Your assistant name",
    domain_risk_level="high",
)

pipeline = EvalPipeline(rubric=rubric, judge_model="gpt-4o")

results = pipeline.run(
    dataset_path="your_questions.json",
    model_responses_path="your_responses.json",
)

results.launch_verdict()
results.gap_analysis()
results.failure_report()

questions file:

[
  {
    "id": "Q001",
    "question": "Your question here",
    "reference_answer": "What a correct answer looks like",
    "category": "optional",
    "difficulty": "easy/medium/hard",
    "domain_risk": "low/medium/high"
  }
]

responses file:
[
  {
    "id": "Q001",
    "response": "The model response to evaluate"
  }
]

output 

LAUNCH READINESS VERDICT
============================================================
Dimension              Score     Threshold     Status
------------------------------------------------------------
accuracy               4.67      4.0           PASS
completeness           4.27      4.0           PASS
grounding              4.13      4.2           FAIL
risk_calibration       4.33      4.2           PASS
clarity                4.87      3.8           PASS

Overall: NOT READY FOR LAUNCH
============================================================

llm-eval-toolkit/
├── README.md
├── core/
│   ├── evaluator.py       <- Evaluation loop and reporting
│   ├── judge.py           <- LLM-as-judge engine
│   └── rubric.py          <- Rubric interface
├── prompts/
│   └── judge_prompt.txt   <- Judge prompt template
├── examples/
│   └── quickstart.py      <- Minimal working example
└── requirements.txt

Key Design Decisions
Rubric-first. Thresholds are configured per use case. What passes for a low-risk chatbot should not pass for a medical or legal assistant.
Gap analysis built in. The framework explicitly tracks where automated evaluation diverges from human judgment — because knowing which dimensions to trust is as important as the scores themselves.
Bring your own data. No dataset is bundled. The framework evaluates whatever you bring to it.
Limitations
	•	Automated judge scores require API access (OpenAI or Anthropic)
	•	Human scores must be provided separately for gap analysis
	•	Statistical reliability requires 50+ examples in production use
License
MIT
This project is independently created using publicly available information and self-generated data. It does not reflect the methods, systems, data, or opinions of any current or former employer.