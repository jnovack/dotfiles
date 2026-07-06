# /manim-init

Scaffold a new Manim animation project using the AnimationMixin architecture.
Read `~/.claude/MANIM.md` before starting — it is the authoritative reference for
all patterns, naming conventions, and known gotchas used below.

---

## Steps

1. **Confirm the target directory.** If the user named a directory, create it.
   If running in an existing empty directory, use it. If a project already exists,
   ask before overwriting.

2. **Ask three questions before writing any files** (combine into a single prompt):
   - What is this animation about? (one sentence — drives node names and visual vocabulary)
   - What are the major visual nodes or actors? (e.g. "User, API Server, Database, Cache")
     They become the `P_` positions and `_setup_*()` methods.
   - Does anything move, travel, or repeat? (e.g. "a request travels from user to server")
     If yes, you will need module-level factory functions — identify what visual form that
     motion takes (a dot, an arrow, a highlighted edge, etc.) and name them accordingly.

3. **Write these five files** in order:

### `_base.py`

Write the full skeleton. Fill in with real node names derived from step 2.
Follow `~/.claude/MANIM.md` exactly for structure and ordering.

The file must contain, in this order:

```
from manim import *

# ── Timing constants ──────────────────────────────────────────────────────────
# Name by what the timing controls — not by what the object being timed is called.
T_TRAVEL     = 2.0    # main element's journey across the scene (if applicable)
T_PAUSE      = 0.25   # hold at waypoints or between beats
T_INTER      = 0.5    # gap between repeated sequences
T_FADE       = 0.3    # fade-in duration for appearing text or elements
T_TITLE_IN   = 0.5
T_TITLE_HOLD = 1.0
# Rename these to match what they control in this specific project.

# ── Colors ────────────────────────────────────────────────────────────────────
# Name by semantic role. Derive the actual hex values from the subject's visual identity.
C_ACTIVE = "#4a9eff"   # primary highlighted / active state
C_OK     = "#44ff66"   # success / healthy / complete
C_FAIL   = "#ff3333"   # error / blocked / broken
# Add role-named colors for anything project-specific (C_PENDING, C_WARN, C_SELECTED…)

# ── Typography ────────────────────────────────────────────────────────────────
# Only define font constants you actually use. Name by role, not by font property.
C_LABEL = "Verdana"    # example — replace with whatever suits the subject
# C_DATA  = "Menlo"    # add only if the project shows code, IPs, or tabular data

# ── Dev mode ──────────────────────────────────────────────────────────────────
DEV_MODE = False

# ── Node positions ────────────────────────────────────────────────────────────
# x: −7 (left) → +7 (right) | y: −4 (bottom) → +4 (top) | z: always 0
# Name from the user's answer to the node question.
P_<NODE_A> = np.array([...])
P_<NODE_B> = np.array([...])

# ── Module-level pure functions ───────────────────────────────────────────────
# Factory functions for this project's visual vocabulary — stateless, return a mobject.
# Do NOT copy _orb() or _path() from the reference project unless your subject
# specifically calls for glowing traveling dots along explicit routes.
# Instead: identify what visual elements your subject needs and implement those.
# Examples by subject:
#   network traffic  → a glowing packet dot, a multi-point travel path
#   data pipeline    → a labeled data chunk, a progress indicator
#   timeline / steps → a milestone marker, a connecting arrow
#   state machine    → a highlighted state box, a transition arc
# Keep these module-level (no self) so they can be called from anywhere.

# ── AnimationMixin ────────────────────────────────────────────────────────────
class AnimationMixin:

    def setup(self):
        super().setup()
        self._setup_<node_a>()
        self._setup_<node_b>()
        self.add(
            # connectors / lines behind everything
            # node boxes
            # labels on top
        )

    # _setup_*() — one method per visual node; assigns to self.*, never calls self.add()
    # _title() and _end_title() — implement to match this project's visual style
    # state_*() — one per act that any later act needs to jump-start from
    # act*() — use phase/act naming (tens digit = phase, units digit = act within phase)
```

Include at least `act01()` as a working skeleton with a `# TODO` title string so
the project can be rendered immediately to verify the scaffold works:

```python
def act01(self):
    t = self._title("TODO: describe this act")
    # TODO: add animation here
    self._end_title(t)
```

Include `state_act01_done(self)` as an empty skeleton with a comment.

### `main.py`

```python
from manim import *
from _base import AnimationMixin

class Phase0(AnimationMixin, Scene):
    def construct(self):
        self.act01()

class FullAnimation(AnimationMixin, Scene):
    def construct(self):
        self.act01()
```

Add Phase classes for each phase implied by the animation subject.
Do NOT include `self.setup()` — Manim calls it automatically.

### `dev_scenes.py`

```python
from manim import *
import _base
_base.DEV_MODE = True
from _base import AnimationMixin

class Act01(AnimationMixin, Scene):
    def construct(self):
        self.act01()
```

One class per act. Acts beyond the first must call the appropriate `state_*()`
methods before calling their act to jump-start the scene state. Follow the
pattern in `~/.claude/MANIM.md`.

### `dev.py`

Copy the standard Jupyter cell runner from `~/.claude/MANIM.md` verbatim.
Add one `%% actNN` commented cell per act defined in `dev_scenes.py`.

### `pyproject.toml`

```toml
[project]
name = "<project-name>"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "manim>=0.18",
]

[tool.uv]
dev-dependencies = [
    "ipykernel",
    "jupyter",
]
```

---

## Rules

- Never put animation logic in `main.py` or `dev_scenes.py`. `construct()` calls only.
- All `self.add()` for persistent objects must be in `setup()`, never in `_setup_*()`.
- Apply the FadeIn/self.add rule from MANIM.md — do not double-add mobs.
- Apply the small-text kerning workaround from MANIM.md for any label under ~14pt.
- Use full parameter names everywhere — no single-letter or abbreviated names in
  method signatures.
- After writing all files, print a quick summary: files created, acts defined,
  nodes defined, and the command to render the first act:
  `uv run manim -ql dev_scenes.py Act01`
