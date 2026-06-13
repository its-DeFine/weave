# App Case Review: Decision Deck

Status: `PASS`
Proof surface: `local deterministic private-app fixture with generated static apps and reviewable framework-gate evidence`
Authority: `recommend_only`
Data boundary: synthetic-only, no external sends, no deployment, no marketing

## Generated app

- App path: `apps/decision-deck/index.html`
- Case review JSON: `apps/decision-deck/review.json`

## Gate summary

- Critical passed: `53`
- Critical failed: `0`
- Warnings: `0`

## Visible gates

- PASS — required_app_files (Evidence)
  - Evidence: `index.html`, `src/app.js`, `src/styles.css`, `public/app-data.json`, `README.md`
  - Detail: index.html, src/app.js, src/styles.css, public/app-data.json, README.md
- PASS — framework_artifacts_complete (Evidence)
  - Evidence: `cognitive-artifacts/intent-frame.json`, `cognitive-artifacts/profile-selection.json`, `cognitive-artifacts/intake-state.json`, `cognitive-artifacts/cwa-work-domain.json`, `cognitive-artifacts/information-requirements.json`, `cognitive-artifacts/missing-information-assessment.json`, `cognitive-artifacts/dmn-routing-table.json`, `cognitive-artifacts/decision-evaluation-log.json`, `cognitive-artifacts/ibis-issue-map.json`, `cognitive-artifacts/open-issues.json`, `cognitive-artifacts/adr-0001-local-private-first.md`, `cognitive-artifacts/decision-register.json`, `cognitive-artifacts/premortem-report.json`, `cognitive-artifacts/risk-to-test-map.json`, `cognitive-artifacts/action-intent.json`, `cognitive-artifacts/action-result.json`, `cognitive-artifacts/proof-boundary-report.json`, `cognitive-artifacts/lifecycle-transition-log.jsonl`, `cognitive-artifacts/prov-ledger.jsonl`
  - Detail: 19
- PASS — no_network_or_dom_injection_terms (QA)
  - Evidence: `src/app.js`
  - Detail: fetch(, XMLHttpRequest, sendBeacon, localStorage, innerHTML
- PASS — app_data_parseable (Evidence)
  - Evidence: `public/app-data.json`
  - Detail: parseable JSON
- PASS — external_actions_disabled (DMN)
  - Evidence: `public/app-data.json`
  - Detail: external_actions_enabled=false
- PASS — marketing_excluded (DMN)
  - Evidence: `public/app-data.json`
  - Detail: marketing_included=false
- PASS — enough_private_sample_signals (CWA)
  - Evidence: `public/app-data.json`
  - Detail: 3
- PASS — intent_frame_parseable (Intent)
  - Evidence: `cognitive-artifacts/intent-frame.json`
  - Detail: parseable JSON
- PASS — profile_selection_parseable (Profile)
  - Evidence: `cognitive-artifacts/profile-selection.json`
  - Detail: parseable JSON
- PASS — intake_state_parseable (Evidence)
  - Evidence: `cognitive-artifacts/intake-state.json`
  - Detail: parseable JSON
- PASS — cwa_parseable (CWA)
  - Evidence: `cognitive-artifacts/cwa-work-domain.json`
  - Detail: parseable JSON
- PASS — information_requirements_parseable (CWA)
  - Evidence: `cognitive-artifacts/information-requirements.json`
  - Detail: parseable JSON
- PASS — missing_information_parseable (CWA)
  - Evidence: `cognitive-artifacts/missing-information-assessment.json`
  - Detail: parseable JSON
- PASS — dmn_parseable (DMN)
  - Evidence: `cognitive-artifacts/dmn-routing-table.json`
  - Detail: parseable JSON
- PASS — decision_log_parseable (DMN)
  - Evidence: `cognitive-artifacts/decision-evaluation-log.json`
  - Detail: parseable JSON
- PASS — ibis_parseable (IBIS)
  - Evidence: `cognitive-artifacts/ibis-issue-map.json`
  - Detail: parseable JSON
- PASS — open_issues_parseable (IBIS)
  - Evidence: `cognitive-artifacts/open-issues.json`
  - Detail: parseable JSON
- PASS — decision_register_parseable (ADR)
  - Evidence: `cognitive-artifacts/decision-register.json`
  - Detail: parseable JSON
- PASS — premortem_parseable (Premortem)
  - Evidence: `cognitive-artifacts/premortem-report.json`
  - Detail: parseable JSON
- PASS — risk_to_test_map_parseable (Premortem)
  - Evidence: `cognitive-artifacts/risk-to-test-map.json`
  - Detail: parseable JSON
- PASS — action_intent_parseable (Action)
  - Evidence: `cognitive-artifacts/action-intent.json`
  - Detail: parseable JSON
- PASS — action_result_parseable (Action)
  - Evidence: `cognitive-artifacts/action-result.json`
  - Detail: parseable JSON
- PASS — proof_boundary_parseable (Proof)
  - Evidence: `cognitive-artifacts/proof-boundary-report.json`
  - Detail: parseable JSON
- PASS — lifecycle_transition_log_parseable (DMN)
  - Evidence: `cognitive-artifacts/lifecycle-transition-log.jsonl`
  - Detail: 5 JSONL events
- PASS — prov_ledger_parseable (PROV)
  - Evidence: `cognitive-artifacts/prov-ledger.jsonl`
  - Detail: 14 JSONL events
- PASS — cross_artifact_identity_consistency (Evidence)
  - Evidence: `cognitive-artifacts/*.json`
  - Detail: decision-deck
- PASS — intent_frame_proof_boundary (Proof)
  - Evidence: `cognitive-artifacts/intent-frame.json`
  - Detail: local deterministic private-app fixture with generated static apps and reviewable framework-gate evidence
- PASS — recommend_only_authority (DMN)
  - Evidence: `cognitive-artifacts/profile-selection.json`
  - Detail: recommend_only
- PASS — required_framework_stack_selected (Profile)
  - Evidence: `cognitive-artifacts/profile-selection.json`
  - Detail: cwa_discovery, dmn_decision_table, ibis_issue_map, adr_decision_record, premortem_review, prov_ledger
- PASS — gestalt_optional_deferred (Profile)
  - Evidence: `cognitive-artifacts/profile-selection.json`
  - Detail: selected=['cwa_discovery', 'dmn_decision_table', 'ibis_issue_map', 'adr_decision_record', 'premortem_review', 'prov_ledger']; optional=['gestalt']
- PASS — cwa_private_constraints_consumed (CWA)
  - Evidence: `cognitive-artifacts/cwa-work-domain.json`
  - Detail: local-only, no public claims, reviewable artifacts, synthetic sample data
- PASS — cwa_observations_match_app_data (CWA)
  - Evidence: `cognitive-artifacts/cwa-work-domain.json`, `public/app-data.json`
  - Detail: observations match sample_data
- PASS — information_requirements_classified (CWA)
  - Evidence: `cognitive-artifacts/information-requirements.json`
  - Detail: present, present_synthetic
- PASS — cwa_missing_information_gate (CWA)
  - Evidence: `cognitive-artifacts/missing-information-assessment.json`
  - Detail: required_missing=[]
- PASS — dmn_local_only_routing (DMN)
  - Evidence: `cognitive-artifacts/dmn-routing-table.json`
  - Detail: {'id': 'DMN-002', 'if': 'private data domain and no approval for external actions', 'result': 'passed', 'then': 'generate local static app only'}
- PASS — dmn_marketing_block (DMN)
  - Evidence: `cognitive-artifacts/dmn-routing-table.json`
  - Detail: {'id': 'DMN-004', 'if': 'marketing stage requested in this evaluation', 'result': 'not_requested', 'then': 'block and record non-claim'}
- PASS — dmn_reviewable_proof_rule (DMN)
  - Evidence: `cognitive-artifacts/dmn-routing-table.json`
  - Detail: DMN-001, DMN-002, DMN-003, DMN-004, DMN-005
- PASS — dmn_transition_gate (DMN)
  - Evidence: `cognitive-artifacts/decision-evaluation-log.json`
  - Detail: 5 evaluations
- PASS — ibis_local_static_preferred (IBIS)
  - Evidence: `cognitive-artifacts/ibis-issue-map.json`
  - Detail: local static app
- PASS — ibis_no_unwaived_blockers (IBIS)
  - Evidence: `cognitive-artifacts/ibis-issue-map.json`
  - Detail: []
- PASS — open_issues_no_blocking_without_waiver (IBIS)
  - Evidence: `cognitive-artifacts/open-issues.json`
  - Detail: []
- PASS — adr_accepted (ADR)
  - Evidence: `cognitive-artifacts/adr-0001-local-private-first.md`
  - Detail: Status: accepted
- PASS — adr_local_private_decision (ADR)
  - Evidence: `cognitive-artifacts/adr-0001-local-private-first.md`
  - Detail: local/static/non-claim text present
- PASS — decision_register_covers_implementation (ADR)
  - Evidence: `cognitive-artifacts/decision-register.json`
  - Detail: [{'artifact': 'adr-0001-local-private-first.md', 'covers': ['implementation_surface', 'data_boundary', 'external_action_boundary'], 'decision': 'build a dependency-free local static app from synthetic private-domain rows', 'id': 'ADR-0001', 'status': 'accepted'}]
- PASS — premortem_failure_modes_classified (Premortem)
  - Evidence: `cognitive-artifacts/premortem-report.json`
  - Detail: 3
- PASS — risk_to_test_map_complete (Premortem)
  - Evidence: `cognitive-artifacts/risk-to-test-map.json`
  - Detail: [{'risk_id': 'RISK-001', 'test_gate': 'proof_boundary_non_claims'}, {'risk_id': 'RISK-002', 'test_gate': 'no_network_or_dom_injection_terms'}, {'risk_id': 'RISK-003', 'test_gate': 'cwa_missing_information_gate'}]
- PASS — action_intent_scope_local_only (Action)
  - Evidence: `cognitive-artifacts/action-intent.json`
  - Detail: write local files under scenario output run syntax and artifact checks
- PASS — action_intent_blocks_external_actions (Action)
  - Evidence: `cognitive-artifacts/action-intent.json`
  - Detail: deployment, external sends, marketing publish, network calls, payments, real private data
- PASS — action_result_generated_files_match (Action)
  - Evidence: `cognitive-artifacts/action-result.json`
  - Detail: README.md, index.html, public/app-data.json, src/app.js, src/styles.css
- PASS — action_result_claim_limits (Proof)
  - Evidence: `cognitive-artifacts/action-result.json`
  - Detail: ['deterministic local fixture/runtime proof only; not live Hermes CLI proof', 'not Telegram, deployed gateway, or hosted application proof', 'no public marketing, analytics calls, payments, auth changes, or external sends', 'uses synthetic private-domain sample data only; no real personal or customer data']
- PASS — proof_boundary_highest_surface (Proof)
  - Evidence: `cognitive-artifacts/proof-boundary-report.json`
  - Detail: local deterministic private-app fixture with generated static apps and reviewable framework-gate evidence
- PASS — proof_boundary_non_claims (Proof)
  - Evidence: `cognitive-artifacts/proof-boundary-report.json`
  - Detail: ['deterministic local fixture/runtime proof only; not live Hermes CLI proof', 'not Telegram, deployed gateway, or hosted application proof', 'no public marketing, analytics calls, payments, auth changes, or external sends', 'uses synthetic private-domain sample data only; no real personal or customer data']
- PASS — proof_boundary_not_proven (Proof)
  - Evidence: `cognitive-artifacts/proof-boundary-report.json`
  - Detail: ['live Hermes-agent lifecycle', 'Codex/Hermes goal-loop execution until acceptance', 'Telegram/deployed-gateway adapter behavior', 'hosted/private-app runtime behavior', 'real user requirement intake', 'real private/customer data handling', 'production/customer/market validation']
- PASS — lifecycle_transitions_cite_dmn (DMN)
  - Evidence: `cognitive-artifacts/lifecycle-transition-log.jsonl`
  - Detail: 5 transitions
- PASS — prov_ledger_required_events (PROV)
  - Evidence: `cognitive-artifacts/prov-ledger.jsonl`
  - Detail: input.normalized, intent.framed, profile.selected, cwa.produced, missing_information.assessed, dmn.evaluated, ibis.produced, premortem.produced, adr.accepted, action.intent_recorded, app.generated, qa.verified, proof.reported, action.result_recorded
- PASS — prov_ledger_event_order (PROV)
  - Evidence: `cognitive-artifacts/prov-ledger.jsonl`
  - Detail: [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13]
- PASS — prov_ledger_entities_exist (PROV)
  - Evidence: `cognitive-artifacts/prov-ledger.jsonl`
  - Detail: []
- PASS — javascript_syntax (QA)
  - Evidence: `src/app.js`
  - Detail: node --check ok

## Explicit non-claims

- deterministic local fixture/runtime proof only; not live Hermes CLI proof
- not Telegram, deployed gateway, or hosted application proof
- no public marketing, analytics calls, payments, auth changes, or external sends
- uses synthetic private-domain sample data only; no real personal or customer data

## Reviewer notes

1. Inspect failed gates first.
2. Open the generated app locally only if UX review is needed.
3. Read `prov-ledger.jsonl` before accepting any proof-surface claim.
4. Verify that CWA/DMN/IBIS/ADR/Premortem/PROV gates consumed artifacts, not just emitted files.
