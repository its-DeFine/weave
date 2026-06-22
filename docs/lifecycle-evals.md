# Lifecycle Evals

WEAVE lifecycle evals are YAML contracts under
`packages/weave-tool/evals/lifecycle/`.

Each eval defines:

- stage name;
- hard gates;
- rubric dimensions;
- evidence requirements;
- minimum score;
- review template.

Use:

```bash
bin/weave eval --list
bin/weave eval engineering --review-template
bin/weave eval engineering --review-file <review.json> --strict
```

Hard gates must be run by the agent when the local environment can run them.
Manual gates are allowed only when the proof is external to the repo.

The release-readiness eval is intentionally strict: it checks operator UX,
repository hygiene, proof quality, side-effect safety, and owner comprehension.
