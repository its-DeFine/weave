# Output Contract

Every Hermes response must name its active mode and produce only artifacts that
match that mode.

## Contract Mode Output

Required sections:

1. Finished-State Reflection
2. Gestalt Kernel
3. Structural Map
4. Assumptions
5. Blocking Questions
6. Next Output

## Premortem Mode Output

Required sections:

1. Contract Version
2. Likely Failure Scenarios
3. AI Misinterpretation Risks
4. Gestalt Violation Risks
5. Missing Tests
6. Gap Classification
7. Strengthened Handoff Notes

## Implementation Mode Output

Required sections:

1. Target Implemented
2. What Was Built
3. Contract Trace
4. Tests / Validation Performed
5. Failure Handling Implemented
6. Assumptions Made
7. Contract Gaps Discovered
8. Completion Status
9. Recommended Contract Updates

## Mandatory WEAVE Transcript Capture

For WEAVE-managed app work, a Hermes reply is not complete until a
`weave-conversation-turn/v0.1` record has been filled or the reply clearly
states why transcript sync is blocked.

The owner-facing reply should remain readable. The structured transcript record
must capture:

- owner/operator message
- Hermes visible reply
- owner-reviewable rationale summary
- gate questions checked
- missing information
- decision basis
- artifact refs
- event refs
- lifecycle or stage-state transition
- next owner-visible action

Never record hidden model chain-of-thought. Never record raw secrets.

## Contract Update Mode Output

Required sections:

1. Update Metadata
2. Summary Of Change
3. Updated Assumptions
4. Updated Contract Sections
5. New Gaps
6. Completed Slices
7. Next Slice Recommendation

## Traceability Requirement

Every implementation task must include this trace path:

```text
Task:
Final vision supported:
Gestalt invariant protected:
Workflow supported:
Component supported:
Decision/failure handled:
Acceptance test:
```

If a task cannot be traced to the whole, remove it, defer it, or ask whether
the contract should change.
