# Verification findings — separate remediation required

No candidate source, policy, approval or manifest was changed. These findings are based on the actual native Chrome saved PDF (`native-NA12878-print.pdf`, page 1 and pages 3–4), API response `browser-api/0020-analyze.body`, and current source bytes.

## P1: unsupported guarantee in the source-checking disclaimer

`app/lib/print/summary_document.dart` `_disclaimer()` says: “Every clinical statement here is machine-checked to trace back to a published CPIC recommendation. That verifies nothing was invented.” The API's generated explanation disclaimer makes the same assurance. This is an unsupported inference: automated provenance checks are not exhaustive verification of every printed sentence or human adjudication. The current gate itself records 55 claims requiring human action and zero approved stored entries. Application limitation text and explanatory Unknown text are also rendered alongside CPIC text.

Invariant: explain the measured automated check accurately without guaranteeing that all clinical wording is supported, invented content is impossible, or human review occurred. A separate minimal content remediation should first preserve these receipts, add a regression for the intended bounded disclaimer, make a proposed wording change, obtain any policy-required exact-byte review, and rerun affected candidate evidence and browser export checks. Do not reuse this candidate's receipts after edits.

## Additional owner review items, not automatically adjudicated

- Page 4 / `app/lib/models/unknown_reason.dart` asserts structural/copy-number changes cannot be represented in a VCF. The application's lack of a validated CYP2D6 structural caller should be described as an application capability boundary; the broad file-format assertion needs source review. No biological definition or calling capability was changed.
- Pages 3–4 describe missing positions as reading as reference. Current application tests and actual outputs show Unknown under incomplete evidence. Clarify the distinction between the upstream hazard and the application's protective evidence gate; avoid implying this app confidently reports missing genotypes.
- Printed summaries omit all 21 raw pipeline warnings and expanded mechanism/variant rationale/patient-friendly text for this run. Current `summary_document.dart` never renders those fields; all six result labels, selected profiles, actions, CPIC population/strength text, Unknown reasons, coverage and provenance are present. JSON exports retain complete scientific fields under the documented transform. This is a disclosed summary scope limitation, not claimed full-response print parity. Owner must decide whether a separate export-policy change is required; this verification does not silently alter it.

The actual copy/download/print mechanisms now have positive browser evidence. Content review remains incomplete. No new synthetic approval or expert status was entered.
