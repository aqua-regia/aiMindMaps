"""Light cleanup for HLD Mermaid diagrams — preserve AI node placement and layer subgraphs."""
import re
from typing import List

INVISIBLE_LAYOUT_RE = re.compile(r"^\s*\w+(?:\s*~~~\s*\w+)+\s*$")


def cleanup_hld_mermaid(content: str) -> str:
    """
    Force flowchart LR and strip legacy invisible rank links.
    Preserves layer subgraphs and node order — placement is left to the AI / Mermaid renderer.
    """
    if not content or "flowchart" not in content.lower():
        return content

    lines = content.split("\n")
    header: List[str] = []
    body: List[str] = []
    in_header = True

    for line in lines:
        stripped = line.strip()
        if not stripped:
            if in_header:
                header.append(line)
            else:
                body.append(line)
            continue

        if in_header and (
            stripped.lower().startswith("flowchart")
            or stripped.startswith("%%")
        ):
            if stripped.lower().startswith("flowchart"):
                header.append("flowchart LR")
            else:
                header.append(line)
            continue

        in_header = False

        if INVISIBLE_LAYOUT_RE.match(stripped):
            continue

        body.append(line.rstrip())

    if not header:
        header = ["flowchart LR"]
    elif not any(l.strip().lower().startswith("flowchart") for l in header):
        header.insert(0, "flowchart LR")

    return "\n".join(header + body)


# Backward-compatible alias
stabilize_hld_layout = cleanup_hld_mermaid
