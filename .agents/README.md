# `.agents/` Skills

These skills provide structured local instructions for AI coding agents to work consistently on this project.

## Structure

```text
.agents/skills/
├── orchestrator/
├── kwgt-kustom/
├── beszel-pocketbase/
├── kustom-data/
├── frontend-visual/
├── charting/
├── test-debug/
└── docs-release/
```

## How to Use

When assigning a task to an agent, specify the skill whenever relevant:

```text
Use .agents/skills/beszel-pocketbase/SKILL.md to validate the endpoint.
```

Or invoke the orchestrator to coordinate multi-skill tasks:

```text
Follow .agents/skills/orchestrator/SKILL.md and implement the chart view.
```

## Design Philosophy

These skills do not pretend KWGT is React or CSS. Instead, frontend engineering principles:
- Visual hierarchy;
- Design tokens;
- Spacing grids;
- Component contracts;
- State machines;
- Accessibility;
- Consistency;

Are translated into native Kustom primitives:
- Overlap groups;
- Stack groups;
- Shapes;
- Progress bars;
- Globals;
- Formulas;
- Touch actions;
- Kustom Flows.
