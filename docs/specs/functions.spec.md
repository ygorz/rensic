# Spec: functions and actions

Repo: rensic-foundry/functions-typescript.
Ship: push stemma, publish version, pin actions.

UI says **file**. Function / action ids below keep early Investigation* names on purpose (see architecture naming note). Do not rename them casually.

## Ontology edits (RensicOntologyEdits)

- `openInvestigation`: Investigation Case + seed CaseAddress per chain.
  Empty title/seed/chains: no-op (no throw).
- `expandInvestigation`: membership role expanded.
- `closeInvestigation` / `archiveInvestigation`: status only.
- `deleteInvestigation`: cascade-delete CaseAddress + InvestigationNarrative for caseId, then InvestigationCase.
  Keeps global Address + known_entities + ingest datasets.
- `saveInvestigationNarrative`: Narrative + caseSummary copy.

## labelAddress

Not a custom function. UI Flag calls action `label-address`.
Empty label should be rejected by UI validation.
Official vs user label: UI enforces official note-only;
community override is a display rule, not pack mutation.

Do not pin `analyzeRisk` (numeric score) to the UI.
