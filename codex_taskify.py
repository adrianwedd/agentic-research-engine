import re
from pathlib import Path

INPUT = Path("TODO.md")
OUTPUT = Path("codex_tasks.md")

def normalize_task_block(block):
    lines = block.strip().splitlines()
    title = lines[0].strip("# ").strip()
    goal = ""
    tasks = []
    accept = []

    # Simple heuristics
    for line in lines[1:]:
        line = line.strip()
        if "goal" in line.lower():
            goal += line.split(":", 1)[-1].strip() + " "
        elif re.match(r"- \[.\] ", line):
            tasks.append(line)
        elif "acceptance" in line.lower():
            accept.append(line)
        elif line.startswith("- "):
            tasks.append(line)

    # Normalize to ticket
    ticket = f"""## {title}

**Goal:** {goal.strip() or 'N/A'}

**Tasks:**
{chr(10).join(tasks or ['- [ ] Define tasks...'])}

**Acceptance Criteria:**
{chr(10).join(accept or ['- [ ] Define acceptance tests...'])}
"""
    return ticket.strip()

def main():
    content = INPUT.read_text()
    blocks = re.split(r"\n(?=#+ )", content)
    results = [normalize_task_block(b) for b in blocks if b.strip()]
    OUTPUT.write_text("\n\n".join(results))
    print(f"✅ Parsed {len(results)} ticket(s) to {OUTPUT}")

if __name__ == "__main__":
    main()