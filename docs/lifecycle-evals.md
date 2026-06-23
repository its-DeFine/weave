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

The Research eval is product-research aware. When product uncertainty is
material, Research must cover product-market facts, target users and use cases,
customer or audience segment, alternatives and substitutes, competitors and
antagonists, disconfirming evidence, constraints and risk gates, technical
feasibility evidence, source list, and separated facts, assumptions, and
opinions. `primitive-market-research` is the relevant skill before Selection in
that case. Technical feasibility evidence alone cannot advance Research while
product, user, customer, alternative, substitute, competitor, antagonist, or
value uncertainty remains central.

The release-readiness eval is intentionally strict: it checks operator UX,
repository hygiene, proof quality, side-effect safety, and owner comprehension.
