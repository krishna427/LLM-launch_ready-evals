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

