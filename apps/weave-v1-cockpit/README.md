# WEAVE v0.1 Chief of Staff Cockpit

This is a static public demo of the WEAVE Chief of Staff operating layer. It is
not the primary product surface. The primary surface stays Codex, Hermes, or
both; this cockpit visualizes the same state model for review, demos, and video
proof.

## What It Shows

- one pinned Chief of Staff home;
- active app and lifecycle stage;
- Codex and Hermes worker lanes;
- proof and blocker trays;
- update inbox behavior;
- local-safe hard gates;
- the distinction between `READY_FOR_REVIEW` and `DONE`.

## Run Locally

```bash
python3 -m http.server 8765 --directory apps/weave-v1-cockpit
```

Open the served address in a browser. The app is static and does not contact
external services.

## CLI State Path

The matching local state command is:

```bash
bin/weave chief-of-staff init --home runs/chief-of-staff-demo --app-id punch-compute --app-name "Punch Compute" --surface both --write
bin/weave chief-of-staff snapshot --home runs/chief-of-staff-demo --out runs/chief-of-staff-demo/snapshot.html
```

Those commands create public-safe local state and a proof snapshot. They do not
collect credentials, deploy, send public messages, or claim live Hermes runtime
access.
