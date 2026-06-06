# FableFrame Studio Product Proof

Status: local product proof, Vercel-ready, not live-deployed

FableFrame Studio is a small Month 1 proof application created to exercise the
WEAVE app lifecycle with an actual web product instead of only runtime docs.

## Application

- Source: `apps/fableframe-studio/`
- App type: static web tool
- Runtime: browser-only HTML, CSS, JavaScript, and canvas
- Deployment target: Vercel static site
- Live deployment state: not deployed
- Monetization state: checkout disabled by default, configurable through
  `public/config.json`

The app lets a reviewer create a visual-novel pitch from a short brief, inspect
generated scenes, export JSON, review KPI estimates, and apply mocked feedback
for one iteration.

## Lifecycle Coverage

The product proof script rehearses the app through:

1. Intent
2. Research
3. Selection
4. Plan
5. Engineering
6. QA
7. KPI Setup
8. Marketing
9. Iteration

It then advances to Analysis and stops there. Analysis remains collecting
because real outcome, live monetization, and usage evidence have not been
created.

## QA

Run:

```bash
python3 scripts/month1_product_app_qa.py --app-dir apps/fableframe-studio
```

The QA script verifies:

- required app files
- Vercel config
- checkout disabled by default
- JavaScript syntax
- deterministic story generation
- mocked feedback iteration
- checkout can be enabled by HTTPS config
- local HTTP serving
- WEAVE lifecycle approval and advance behavior for this app

The generated JSON report is written to the operator's local Codex artifact
directory and should be attached or summarized for review.

## Live Gaps

- No Vercel URL has been created yet.
- No real payment or checkout provider has been connected.
- No public marketing send has been performed.
- No real user KPI or monetization evidence exists yet.

Those are live external effects and require explicit owner approval before
execution.
