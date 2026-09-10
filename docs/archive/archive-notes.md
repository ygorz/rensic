# Archive notes (from retired STUDY-GUIDE / ontology-redesign)

The August 2026 study guide and ontology-redesign notes at this folder root were retired when the living docs moved under `docs/`. Most product guidance is superseded by [README.md](README.md), [ontology.md](ontology.md), [map.md](map.md), and [status.md](status.md). Unique historical bits kept here:

## RID cheat sheet (Foundry)

| Thing | RID / path |
|---|---|
| Project folder | `ri.compass.main.folder.6a76fd15-beab-4ec7-bd0e-9ae449b52375` |
| Ontology | `ri.ontology.main.ontology.008c2810-1577-4cb8-921f-6843efb36695` |
| Address | `ri.ontology.main.object-type.78b57acd-cd97-43c3-b3c6-aa5b56e2d275` |
| Case Address | `ri.ontology.main.object-type.ecd3489e-d615-47c8-bc50-0093a02e2c9b` |
| Investigation Case | `ri.ontology.main.object-type.67c2b62c-59d8-4097-842d-6bbff4b747b9` |
| Investigation Narrative | `ri.ontology.main.object-type.61fcbc96-eff6-4b48-9967-e4c48c1f9b40` |
| Transaction | `ri.ontology.main.object-type.e6628e26-edad-46a7-9a4d-b88dc4566f3f` |
| Token Transfer | `ri.ontology.main.object-type.f43ec335-4a87-4f38-939f-4c6bd6b6e310` |
| Token-contract link | `ri.ontology.main.relation.d4bef523-a3ba-43ad-9b34-4554b969f05c` |
| Functions stemma | `ri.stemma.main.repository.3510bc15-8b1d-46ba-bd56-1d64c5dcd698` |
| Ingest stemma | `ri.stemma.main.repository.62965e3e-8236-4a2f-a3de-c49ec2093a68` |
| `investigationCaseGraph` | `ri.function-registry.main.function.81c0a103-d122-43ee-b96c-1826ab8b2331` |
| `openInvestigation` | `ri.function-registry.main.function.f29ebe14-d0c8-41bd-87ec-88e33aedf12f` |
| `expandInvestigation` | `ri.function-registry.main.function.519a9a18-d571-48f8-a177-78c03a170ebf` |
| `saveInvestigationNarrative` | `ri.function-registry.main.function.9510302a-b957-4db1-8160-6e8a90eafe68` |
| Workshop module (legacy UI) | `ri.workshop.main.module.032de9d2-87d6-4244-9594-1642629b67ea` |
| Vertex graph | `ri.opus.main.graph.3a5cb370-7c49-498b-b78b-63e9200e3e4a` |
| Alchemy Magritte source | `ri.magritte..source.c55dc141-7169-45ca-8058-c1d727bcd013` |
| Pipeline `case_addresses` | `ri.foundry.main.dataset.b2fcc62d-e1ef-4d4f-a08d-3928543ef941` |

Enrollment host (no secrets): `georgegorzhiyev.usw-17.palantirfoundry.com`. Project path: `/George Gorzhiyev-a8216a/Rensic`.

## Historical case-id remapping

Early demo queue used pipeline id `live-case-001` while the Ontology Investigation Case PK was UUID `3cf7174a-fcf2-494c-b4bc-16c66fc6ea6f`. `config.LEGACY_PIPELINE_CASE_IDS` still remaps that leftover. Prefer letting `openInvestigation` own the UUID end-to-end.

## Design history (one paragraph)

Address was doing identity + case-window observation at once. **Case Address** became membership (role, hop, case-scoped metrics) so two cases sharing a wallet do not overwrite each other. Vertex still styles Address for graph convenience. Palantir MCP could create new types but struggled with two-datasource object updates and Workshop/Vertex; AI FDE closed some of those; Vertex Search Around binding remains a human click in Vertex.

## What to read instead

Living classroom: [README.md](README.md). Architecture: [architecture.md](architecture.md) (umbrella) and [map.md](map.md). Specs: [specs/](specs/).
