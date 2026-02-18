"""
Test 3: Reproduce with TOOLS — the only remaining difference from the real app.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

# ── Instrument LLM.call ────────────────────────────────────────────────────
from crewai.llm import LLM

_original_call = LLM.call

def _instrumented_call(self, messages, *args, **kwargs):
    if isinstance(self.model, str) and "perplexity" in self.model:
        print(f"\n{'='*60}", flush=True)
        print(f"[DEBUG] LLM.call #{getattr(_instrumented_call, '_count', 0)} for {self.model}", flush=True)
        _instrumented_call._count = getattr(_instrumented_call, '_count', 0) + 1
        if isinstance(messages, list):
            for i, msg in enumerate(messages):
                role = msg.get("role", "?")
                content = msg.get("content")
                if content is None:
                    print(f"  [{i}] role={role} content=None  <<<< EMPTY!", flush=True)
                elif isinstance(content, str) and content.strip() == "":
                    print(f"  [{i}] role={role} content=''  <<<< EMPTY STRING!", flush=True)
                elif isinstance(content, list) and len(content) == 0:
                    print(f"  [{i}] role={role} content=[]  <<<< EMPTY LIST!", flush=True)
                elif isinstance(content, str):
                    preview = content[:200].replace('\n', '\\n')
                    print(f"  [{i}] role={role} len={len(content)} preview={preview!r}", flush=True)
                else:
                    print(f"  [{i}] role={role} type={type(content).__name__}", flush=True)
        print(f"{'='*60}\n", flush=True)
    return _original_call(self, messages, *args, **kwargs)

LLM.call = _instrumented_call

# ── Import the REAL tools ───────────────────────────────────────────────────
from backend.tools import WebResearchTool, DependencyCheckTool
from crewai import Agent, Task, Crew

# DX Analyst WITH tools — matching real config exactly
dx_analyst = Agent(
    role="Developer Experience Analyst",
    goal="Evaluate developer adoption feasibility of proposed technology.",
    backstory="You assess community health, documentation quality, and team readiness.",
    tools=[WebResearchTool(), DependencyCheckTool()],  # <-- THE DIFFERENCE
    allow_delegation=False,
    verbose=True,
    memory=False,
    llm="perplexity/sonar-pro",
)

task = Task(
    description=(
        "Evaluate 'Redis 7.x' for use as a caching layer in the Customer API. "
        "Assess community health, documentation quality, learning curve, and hiring market. "
        "Provide a DX score from 0-100."
    ),
    expected_output="A developer experience assessment with a score from 0-100.",
    agent=dx_analyst,
)

crew = Crew(
    agents=[dx_analyst],
    tasks=[task],
    verbose=True,
    planning=False,
    memory=False,
)

print("\n[TEST 3] DX Analyst + TOOLS (WebResearchTool, DependencyCheckTool)...", flush=True)
try:
    result = crew.kickoff()
    print(f"\n[TEST 3] SUCCESS: {str(result)[:300]}", flush=True)
except Exception as e:
    print(f"\n[TEST 3] FAILED: {type(e).__name__}: {e}", flush=True)
