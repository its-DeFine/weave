# Launch Studio Textual v1

Launch Studio Textual v1 is a local-only static launch readiness cockpit for a founder reviewing lifecycle status, launch risks, QA state, SEO readiness, and launch boundaries before making a launch decision.

## Local Run Steps

1. Open `index.html` directly in a browser from this generated app directory.
2. Review the lifecycle, risk, QA, SEO, and boundary panels.
3. Use the checklists and decision notes to save a local review in browser storage.
4. Use **Clear local review** to remove the saved browser review state.

No install step, backend service, account, credential, or network call is required.

## Hard Boundaries

- No deployment is performed or configured.
- No credentials are requested, stored, or sent.
- No public messages are sent.
- No paid spend is initiated.
- No external APIs are called.
- No analytics beacons are included.
- Review state is stored only in browser `localStorage`.

## Files

- `index.html` contains the semantic app shell and required metadata.
- `src/app.js` contains the local-only cockpit behavior.
- `src/styles.css` contains the responsive app styling.
- `public/config.json` records disabled analytics, deployment, paid spend, public send, and credentials.
