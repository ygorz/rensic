# Spec: entity pack

Canonical CSV: rensic-ingestion/.../data/known_entities.csv
UI copy: rensic-app/src/knownEntities.json

## Columns

Required: chain, address, name, category, source, source_url, tier
Optional: secondary_category

## Tiers

- official: cited (PoR, OFAC, deployment docs). Flag cannot rename.
- community: nametags with caveat. A user-set display label may win.
- Conflict: official wins; community row suppressed.

## Person first-party rule

Person category requires a first-party citation
(e.g. vitalik.ca). No Arkham dumps. Prefer few official persons.

## Address rules

- Addresses stored lowercase 0x hex.
- Dedupe on chain+address.
- Names and sources non-empty for shipping rows.
- tier must be official or community.
- See SOURCES.md for citation bible.
