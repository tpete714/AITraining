"""Setup script for the Review + Refactor Agent training demo.

Run this to add the bulk_import.py file to the repo and wire it into
main.py. This creates the "bad code" state that the review/refactor
subagent pipeline operates on.

Usage:
    python .github/scripts/setup_review_refactor_lab.py
"""
import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sample_bulk_import_target import BULK_IMPORT_FILE_CONTENT


def main():
    bulk_import_path = os.path.join(REPO_ROOT, "src", "bulk_import.py")
    with open(bulk_import_path, "w", encoding="utf-8") as f:
        f.write(BULK_IMPORT_FILE_CONTENT)
    print(f"Created: {bulk_import_path}")

    main_path = os.path.join(REPO_ROOT, "src", "main.py")
    with open(main_path, "r", encoding="utf-8") as f:
        content = f.read()

    if "from .bulk_import import router" not in content:
        content = content.replace(
            "from .schemas import",
            "from .bulk_import import router as bulk_import_router\nfrom .schemas import",
        )
        content = content.replace(
            "@app.get(\"/health\")",
            "app.include_router(bulk_import_router)\n\n\n@app.get(\"/health\")",
        )
        with open(main_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Updated: {main_path} (added bulk_import router)")
    else:
        print(f"Skipped: {main_path} (already has bulk_import router)")

    print("\nSetup complete. Run 'pytest' to verify the existing suite still passes.")
    print("Next: dispatch the review subagent using .github/scripts/agent-briefs/review-brief.md")


if __name__ == "__main__":
    main()
