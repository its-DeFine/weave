# Launch Studio Textual v1

Launch Studio Textual v1 is a local-only static cockpit for reviewing launch readiness before a founder decides to hold, limit, or launch.

## Local Run

1. Open `index.html` in a browser.
2. Optionally serve this folder with any static file server and open the address printed by that tool.
3. Review lifecycle, risk, QA, SEO, and boundary states.
4. Save the decision memo. The app stores review state only in browser local storage.

## Hard Boundaries

- No deployment is performed.
- No credentials are requested, stored, or transmitted.
- No public messages are sent.
- No paid spend is triggered.
- No external APIs are called.
- No analytics beacons are included.
- No redirects are used.

## Files

- `index.html` provides the semantic page shell, metadata, stylesheet link, and script tag.
- `src/app.js` implements local state, review controls, and persistence.
- `src/styles.css` defines the cockpit layout and responsive presentation.
- `public/config.json` records disabled capabilities for analytics, deployment, paid spend, public sends, and credentials.
