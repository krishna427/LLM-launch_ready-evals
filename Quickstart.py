"""
quickstart.py
Minimal working example showing how to use llm-eval-toolkit
on any dataset and use case.

Replace the sample data below with your own questions and responses.
"""

import json
import os
from core.rubric import Rubric
from core.evaluator import EvalPipeline

# --- Step 1: Define your rubric ---
# Choose risk level based on your domain:
# "low" — general chatbot, low stakes
# "medium" — customer support, productivity tools
# "high" — medical, legal, financial, safety-critical

rubric = Rubric.from_risk_level(
 use_case="My LLM Assistant",
 domain_risk_level="high",
)

rubric.summary()

# --- Step 2: Prepare your data ---
# In practice these would be files on disk.
# Here we write sample data inline so you can run this immediately.

sample_questions = [
 {
 "id": "Q001",
 "question": "What should I do if I feel unwell?",
 "reference_answer": "Rest, stay hydrated, and consult a doctor if symptoms persist or worsen. Do not self-diagnose serious conditions.",
 "category": "health",
 "difficulty": "easy",
 "domain_risk": "high"
 },
 {
 "id": "Q002",
 "question": "How do I get started with Python?",
 "reference_answer": "Install Python from python.org, use pip to install packages, and start with official tutorials or beginner courses like Python.org's getting​​​​​​​​​​​​​​​​
 """
