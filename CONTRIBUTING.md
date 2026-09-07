# Contributing

Project home: ~/Documents/WilderformTools/rensic/

## Git rules

- Umbrella git tracks docs/README/specs only.
- Nested package dirs are gitignored by the umbrella.
- Each package keeps its own stemma .git and origin.
- Do not squash histories or rewrite remotes.
- Do not print remote URLs (they embed tokens).

## Never commit

- .env.development and other env files
- Untitled/, node_modules/, .maestro/, secrets

## Tests before push

- App: vitest, tsc, eslint
- Functions: jest under functions-typescript
- Ingestion: pytest under transforms-python

Reopen Cursor windows on new folder paths after a move.
