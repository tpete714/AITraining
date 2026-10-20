"""Run the AI PR Review locally for demo purposes (no GitHub Actions needed).

Usage:
    set ANTHROPIC_API_KEY=sk-ant-...
    python .github/scripts/demo_review_local.py

Uses the sample bad PR diff to demonstrate the review agent.
"""
import json
import sys
from pathlib import Path

try:
    import anthropic
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "anthropic"])
    import anthropic

# Load sample diff
sys.path.insert(0, str(Path(__file__).parent))
from sample_bad_pr import SAMPLE_DIFF

# Load standards
agents_md = Path(__file__).resolve().parent.parent.parent / "AGENTS.md"
standards = agents_md.read_text(encoding="utf-8") if agents_md.exists() else ""

coding_standards = Path(__file__).parent / "coding_standards.md"
if coding_standards.exists():
    standards += "\n\n" + coding_standards.read_text(encoding="utf-8")

SYSTEM = """You are a senior code reviewer for a Python FastAPI project.
You review pull requests against the project's coding standards.

Your review must cover:
1. CORRECTNESS: Logic errors, off-by-one, missing edge cases
2. SECURITY: SQL injection, input validation gaps, secrets in code
3. STANDARDS: Does code follow project conventions from AGENTS.md?
4. TESTS: Are new paths tested? Do tests cover edge cases?
5. PERFORMANCE: N+1 queries, unnecessary loops, missing indexes

Output format (strict JSON):
{
  "summary": "2-3 sentence overall assessment",
  "verdict": "approve" | "request_changes",
  "findings": [
    {
      "severity": "critical" | "warning" | "nit",
      "file": "path/to/file.py",
      "line": 42,
      "title": "Short title",
      "detail": "What's wrong and how to fix it"
    }
  ],
  "tests_assessment": "Are tests sufficient? What's missing?",
  "security_notes": "Any security concerns?"
}
"""

USER = f"""Review this Pull Request.

## PR Info
Title: Add bulk import and search endpoints
Description: Adds two new endpoints for importing assets in bulk and searching by name.

## Test Results
Exit code: 0 (PASSED - existing tests still pass, but no new tests added)

## Project Standards
```
{standards}
```

## Diff
```diff
{SAMPLE_DIFF}
```
"""

print("=" * 60)
print("AI PR REVIEW AGENT - LOCAL DEMO")
print("=" * 60)
print()
print("Sending diff to Claude for review...")
print()

client = anthropic.Anthropic()
message = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=2000,
    messages=[{"role": "user", "content": USER}],
    system=SYSTEM,
)

response_text = message.content[0].text
clean = response_text.strip()
if clean.startswith("```"):
    clean = clean.split("\n", 1)[1]
    clean = clean.rsplit("```", 1)[0]

review = json.loads(clean)

# Pretty print
verdict = review.get("verdict", "unknown")
print(f"VERDICT: {'APPROVE' if verdict == 'approve' else 'CHANGES REQUESTED'}")
print()
print(f"Summary: {review.get('summary', '')}")
print()

print(f"Findings ({len(review.get('findings', []))}):")
print("-" * 40)
for f in review.get("findings", []):
    sev = f["severity"].upper()
    icon = {"CRITICAL": "[!!!]", "WARNING": "[!]", "NIT": "[~]"}.get(sev, "[?]")
    print(f"  {icon} {sev}: {f['title']}")
    print(f"      File: {f['file']} line {f.get('line', '?')}")
    print(f"      {f['detail']}")
    print()

print("Tests Assessment:", review.get("tests_assessment", "N/A"))
print()
print("Security Notes:", review.get("security_notes", "N/A"))
print()

critical = sum(1 for f in review.get("findings", []) if f["severity"] == "critical")
if critical > 0:
    print(f"ACTION: Would create Change Request issue ({critical} critical findings)")
else:
    print("ACTION: Would approve PR and deploy to dev")

print()
print("=" * 60)
print("DEMO COMPLETE")
print("=" * 60)
