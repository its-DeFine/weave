# WEAVE Review Loop Process

The WEAVE review loop is mandatory before a lifecycle slice is accepted.

```text
observe -> validate -> govern -> review -> sync
```

## 1. Observe

Record the changed files, created artifacts, commands run, and current lifecycle
state.

## 2. Validate

Run the smallest checks that prove the slice. For code this usually includes
unit tests, smoke tests, static scans, or a local artifact open/readback.

## 3. Govern

Compare the proof against the requested scope and stop boundaries. Do not allow
scope drift to become an invisible claim.

## 4. Review

Return one of:

- `ACCEPT_FOR_SCOPE`: the requested slice is proven.
- `REVISE`: the slice is not good enough and can be improved locally.
- `BLOCKED`: progress is blocked by an external or unavailable dependency.
- `NEEDS_OWNER_ACTION`: the next step crosses a real owner boundary.

## 5. Sync

Update `lifecycle.json`, `todos.md`, `proof/`, `blockers/`, `review/`, and
`updates/readback.json` so the next thread can resume without guessing.

## Non-Claims

The review loop never upgrades local proof into public, paid, credentialed, or
deployed proof. Those require their own stage, authorization, and evidence.
