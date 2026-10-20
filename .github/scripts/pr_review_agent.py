"""AI PR Review Agent - called from GitHub Actions.

Reads PR diff + test results, calls Claude API, posts review comments.
Creates a Change Request issue if tests fail or critical findings exist.
"""
import json
import os
import subprocess
import sys
from pathlib import Path

try:
    import anthropic
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "anthropic"])
    import anthropic

PR_NUMBER = os.environ["PR_NUMBER"]
PR_TITLE = os.environ.get("PR_TITLE", "")
PR_BODY = os.environ.get("PR_BODY", "")
REPO = os.environ["REPO"]
TEST_EXIT_CODE = os.environ.get("TEST_EXIT_CODE", "1")
GH_TOKEN = os.environ["GH_TOKEN"]

# Read inputs
diff_text = Path("pr-diff.txt").read_text(encoding="utf-8", errors="replace")[:12000]
test_output = Path("test-output.txt").read_text(encoding="utf-8", errors="replace")[:3000]

# Read project standards from AGENTS.md
agents_md = ""
if Path("AGENTS.md").exists():
    agents_md = Path("AGENTS.md").read_text(encoding="utf-8")[:4000]

# Build the review prompt
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
Title: {PR_TITLE}
Description: {PR_BODY or '(none)'}

## Test Results
Exit code: {TEST_EXIT_CODE} ({'PASSED' if TEST_EXIT_CODE == '0' else 'FAILED'})
```
{test_output}
```

## Project Standards (AGENTS.md)
```
{agents_md}
```

## Diff
```diff
{diff_text}
```
"""

# Call Claude API
client = anthropic.Anthropic()
message = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=2000,
    messages=[{"role": "user", "content": USER}],
    system=SYSTEM,
)

response_text = message.content[0].text

# Parse JSON from response (handle markdown code fences)
clean = response_text.strip()
if clean.startswith("```"):
    clean = clean.split("\n", 1)[1]
    clean = clean.rsplit("```", 1)[0]
review = json.loads(clean)

# Build review comment
findings_md = ""
critical_count = 0
for f in review.get("findings", []):
    sev = f["severity"]
    icon = {"critical": "🔴", "warning": "🟡", "nit": "🔵"}.get(sev, "⚪")
    findings_md += f"\n### {icon} {sev.upper()}: {f['title']}\n"
    findings_md += f"**{f['file']}** (line {f.get('line', '?')})\n\n"
    findings_md += f"{f['detail']}\n"
    if sev == "critical":
        critical_count += 1

tests_passed = TEST_EXIT_CODE == "0"
verdict = review.get("verdict", "request_changes")

comment_body = f"""## AI PR Review Agent

### Verdict: {'✅ APPROVE' if verdict == 'approve' else '❌ CHANGES REQUESTED'}

{review.get('summary', '')}

### Test Results: {'✅ Passed' if tests_passed else '❌ Failed'}

### Findings ({len(review.get('findings', []))} items)
{findings_md if findings_md else '_No issues found._'}

### Tests Assessment
{review.get('tests_assessment', 'N/A')}

### Security Notes
{review.get('security_notes', 'N/A')}

---
_Review by AI PR Review Agent (Claude Sonnet) | [View workflow run](https://github.com/{REPO}/actions)_
"""

# Post review comment
subprocess.run([
    "gh", "pr", "comment", PR_NUMBER, "--body", comment_body
], check=True, env={**os.environ, "GH_TOKEN": GH_TOKEN})

# If critical issues or tests failed, create a Change Request issue
if critical_count > 0 or not tests_passed:
    cr_title = f"CR: Review findings for PR #{PR_NUMBER} - {PR_TITLE}"
    cr_body = f"""## Change Request - AI Review Findings

**PR:** #{PR_NUMBER} - {PR_TITLE}
**Tests:** {'Passed' if tests_passed else 'FAILED'}
**Critical findings:** {critical_count}
**Total findings:** {len(review.get('findings', []))}

### Action Required
{'- [ ] Fix failing tests' if not tests_passed else ''}
"""
    for f in review.get("findings", []):
        if f["severity"] == "critical":
            cr_body += f"- [ ] Fix: {f['title']} in {f['file']}\n"

    cr_body += f"""
### Review Summary
{review.get('summary', '')}

### Linked PR
#{PR_NUMBER}

---
_Auto-created by AI PR Review Agent_
"""

    subprocess.run([
        "gh", "issue", "create",
        "--title", cr_title,
        "--body", cr_body,
        "--label", "change-request,ai-review",
    ], check=True, env={**os.environ, "GH_TOKEN": GH_TOKEN})
    print(f"Created Change Request issue for PR #{PR_NUMBER}")

# Set PR review status
if verdict == "approve" and tests_passed:
    subprocess.run([
        "gh", "pr", "review", PR_NUMBER, "--approve",
        "--body", "AI Review Agent: All checks passed. Approved."
    ], check=True, env={**os.environ, "GH_TOKEN": GH_TOKEN})
    print("PR approved")
else:
    subprocess.run([
        "gh", "pr", "review", PR_NUMBER, "--request-changes",
        "--body", f"AI Review Agent: {critical_count} critical findings. Tests {'passed' if tests_passed else 'failed'}."
    ], check=True, env={**os.environ, "GH_TOKEN": GH_TOKEN})
    print("Changes requested")

print(f"Review posted. Verdict: {verdict}. Findings: {len(review.get('findings', []))}")
