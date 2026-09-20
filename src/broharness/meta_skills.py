"""Loads the harness's own bundled meta-skills (skill-call, tool-call) --
these carry the tool-calling protocol prompt itself, not user content, so
they live inside the broharness package (default_skills/), not the user's
skills/ folder, and are always present regardless of what a user's own
skills directory contains.

Previously these were loaded the same way as any user skill, via
SkillControl.load_skill(skill_name) against the user's skill_dir. That has
a real failure mode: SkillControl.load_skill returns None (not an
exception) for a name that doesn't exist under that directory, so an empty
or meta-skill-less skills/ folder silently dropped the entire tool-use
contract from the prompt with no error anywhere -- the model would then
have to guess the required JSON format from nothing, reliably burning
through several retries (or worse, never landing on it).
"""
from pathlib import Path

from broskill.processing.skill import split_frontmatter

DEFAULT_SKILLS_DIR = Path(__file__).parent / "default_skills"


def load_meta_skill(name: str) -> str:
    """Returns one bundled meta-skill's SKILL.md body (frontmatter
    stripped) -- the same shape SkillControl.load_skill returns for a
    normal skill, so callers don't need to special-case the result."""
    skill_md = DEFAULT_SKILLS_DIR / name / "SKILL.md"
    if not skill_md.is_file():
        raise FileNotFoundError(
            f"bundled meta-skill '{name}' is missing from the broharness "
            f"package (expected {skill_md}) -- this is a packaging bug, "
            f"not something a user's skills/ folder can fix."
        )
    text = skill_md.read_text(encoding="utf-8")
    _, body = split_frontmatter(text)
    return body
