# AGENTS.md

## Repository Instructions

- If this repository also contains `CLAUDE.md`, read it as additional repository-specific guidance.

## TypeScript v1 Functions

- For examples of supported types, Ontology usage, local development, and publishing, consult the repository `README.md`.
- Function code lives under `functions-typescript/src/index.ts`. Functions are class methods decorated with `@Function()` or `@OntologyEditFunction()` from `@foundry/functions-api`.
- Before using Ontology objects or links, verify they are imported into the repository and use generated imports from `@foundry/ontology-api`. Do not invent object API names.

## Workflow

- Prefer the root Gradle wrapper for repository tasks: `./gradlew check`, `./gradlew startDevServer`, `./gradlew localDev`, and publish/tag tasks. For focused Jest tests, run `npm run jest` from `functions-typescript`.
- After editing function code, check diagnostics or run the build, preview changed functions with representative inputs, then run CI before publishing.
