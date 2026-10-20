# Review Subagent Brief

You are reviewing a new file for compliance with this project's coding
standards before it merges.

**Target file:** set by whoever dispatches this brief (e.g. `src/bulk_import.py`).
If no target file was given, ask before proceeding.

## Task

1. Read the target file: the file under review.
2. Read `.github/scripts/coding_standards.md`: the project's coding
   standards (Bad/Good examples included).
3. Read `AGENTS.md`: project conventions.
4. Review the file against every rule in `coding_standards.md`. Cover:
   correctness, security (SQL injection, input validation), standards
   compliance, and whether tests exist for the new endpoints.
5. Write your findings to `docs/pr-pipeline/review-comments.md`, in this format:

   ```markdown
   # Code Review: <target file>

   **Verdict:** approve | request_changes

   ## Summary
   <2-3 sentence overall assessment>

   ## Findings

   ### CRITICAL: <title>
   **File:** <target file> (line <N>)
   <what's wrong and how to fix it>

   ### WARNING: <title>
   ...

   ### NIT: <title>
   ...

   ## Tests Assessment
   <are tests sufficient? what's missing?>

   ## Security Notes
   <any security concerns?>
   ```

6. Convert that same content to `docs/pr-pipeline/review-comments.html`: a minimal
   standalone HTML page (`<html><head><title>...` with a `<style>` block
   for basic readability), headings/lists/bold mapped to real HTML tags,
   not a raw markdown dump in a `<pre>`.

7. Set **Verdict: request_changes** if there is at least one CRITICAL
   finding or the file has zero tests for its new endpoints. Otherwise
   **approve**.

## Report back

State the verdict and the count of findings by severity in your final
message. Do not fix anything: this is a review-only task.
