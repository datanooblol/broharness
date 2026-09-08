"""Skill discovery and loading -- the discover/load stages.

A skill is a folder under bro_skills/ with a SKILL.md: YAML-ish frontmatter
(name, description, and for funnel skills, stage) followed by a free-form
instructions body.
"""
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SKILLS_DIR = REPO_ROOT / "bro_skills"


def parse_skill_md(path: Path) -> dict:
    """Splits a SKILL.md into its frontmatter (flat dict) and body.

    Frontmatter is intentionally simple -- `key: value` lines between two
    `---` fences -- so no yaml dependency is needed.
    """
    text = path.read_text(encoding="utf-8")
    _, frontmatter, body = text.split("---", 2)

    meta = {}
    for line in frontmatter.strip().splitlines():
        key, _, value = line.partition(":")
        meta[key.strip()] = value.strip()

    return {**meta, "body": body.strip(), "path": path}


def discover_skills(skills_dir: Path = SKILLS_DIR) -> dict:
    """Stage 1: cheap discovery. Only name + description (+ stage), for every skill."""
    registry = {}
    for skill_md in sorted(skills_dir.glob("*/SKILL.md")):
        skill = parse_skill_md(skill_md)
        registry[skill["name"]] = {
            "description": skill["description"],
            "stage": skill.get("stage"),
            "path": skill["path"],
        }
    return registry


def load_skill(name: str, registry: dict) -> str:
    """Stage 2: full-body load, only for the requested skill."""
    entry = registry[name]
    skill = parse_skill_md(entry["path"])
    return skill["body"]


def skill_dir(name: str, registry: dict) -> Path:
    return registry[name]["path"].parent
