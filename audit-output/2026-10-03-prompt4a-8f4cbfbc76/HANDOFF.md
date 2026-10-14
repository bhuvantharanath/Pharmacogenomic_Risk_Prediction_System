# Prompt 4A — real human-review handoff

Prepared 3 October 2026. **No adjudication performed. F1 remains open.**

## Start here

1. Read [the complete owner packet](OWNER-REVIEW-PACKET.md), which contains all 20 entries and all 179 current claim occurrences, including the 124 existing human-labelled records. Each entry includes all four exact stored explanation fields, its recommendation, candidate pinned source rows, and content/source/context hashes. Each claim includes its exact sentence, claim key, source aids, automated result, existing record, flags, and required action.
2. Read [primary-source verification](SOURCE-VERIFICATION.md). The local corpus and candidate passages are aids to finding evidence. Neither lexical alignment nor a linked paper establishes that a particular sentence is supported.
3. Fill the applicable rows of [the response template](reviewer-response-template.json). All decision, reviewer identity and review-time fields are blank. Return it as a separate file, with any revised wording separately identified. Do not change the original audit snapshot.
4. Consider [the separate proposed changes](PROPOSED-TEXT-CHANGES.md). Fifteen draft sentence replacements and one citation-metadata proposal are **unreviewed and unapplied**. They do not resolve all flagged concerns.

The machine-readable [inventory](inventory.json) is the definitive packet index. It repeats bindings per claim and preserves complete existing records. [The original store](original-explanations.json) and [original manifest](original-explanation_approvals.json) are byte-for-byte snapshots. No reviewer has been contacted.

## Exact outstanding inventory

| Item | Fresh count | Meaning |
|---|---:|---|
| Current stored entries | 20 | All remain in the declared review set, including codeine/warfarin Unknown |
| Current claim occurrences | 179 | Sentence occurrences; not a count of independent biological propositions |
| Current decisions recorded under a human name | 124 | All say bulk decision, not individually read |
| Automated-only decisions | 36 | Require real human decisions |
| Unresolved escalations | 19 | Require real human decisions |
| Pending claim decisions under the current gate | **55** | 36 + 19; unchanged by this task |
| Rejected current claims | 0 | No new accept/reject decisions were made |
| Entries missing author-read records | **20** | Separate from claim adjudication |
| Approved / runtime-releasable stored entries | **0 / 0** | Empty eligible set is not reviewed |
| Historical records with no current matching claim | 2 | Retained separately; do not count toward 179 or transfer to new text |
| Clinical expert review | **NOT_OBTAINED** | No qualified clinical review was performed |

144 claim occurrences carry a review flag in this packet, including broad context/source reminders. This is automated/editorial triage, **not 144 newly rejected claims or an additional machine-gate count**. Several concerns affect previously bulk-accepted text, so checking only the 55 pending mechanism claims would leave substantive questions unexamined. Use the full entry read to assess them.

## What the historical bindings establish

- All 124 current human-labelled records match the current field and exact extracted sentence. Their keys recompute correctly. Every record is preserved, including the recorded name, rationale and historical timestamp. This task verifies stored records, not the person's identity or whether the historical action actually occurred.
- The claim key is the first 16 hexadecimal characters of SHA-256 over case, field and whitespace-normalized sentence, each followed by NUL. It is **not** a raw-byte hash, a full-entry approval, or a source/context attestation. The packet adds full UTF-8 sentence hashes for checking returned bytes.
- None of those 124 records contains a historical content hash, source hash or semantic-context hash, or a structured reviewed-source reference. Historical source/context review therefore remains **unproven from those records**. A newly computed hash must not be presented as one the person reviewed in July.
- All 20 current manifest content/source/context hashes match recomputation from the current dirty tree. All manifest entries are unresolved. Matching an unresolved projection proves consistency, not human approval.
- Content hashes cover the four explanation fields through canonical JSON. Source hashes cover normalized recommendation text, citation, the current retrieved mechanism snippet (which can be shorter than the whole corpus), and URL. Context hashes cover normalized drug/gene, capability relevant genes, phenotype and normalized label. Whole file hashes and exact fields are separately preserved.
- The context schema has no indication or explicit paired-gene phenotype, and the source hash contains recommendation text rather than a unique source-row ID. Text-equivalent pinned rows can have different lookup keys/populations. All candidate matches are listed without selecting one as historical truth. The reviewer must resolve applicability; this packet does not extend a binding to a new indication, gene combination or source row.
- The two unmatched `simvastatin:Unknown` historical keys are `30677694ad44a8da` and `82991ae0bde1d7ce`. Their old “result was not available” sentences were replaced before this task. They remain archived in the store and packet; they confer no approval on the current “no usable result” sentences.

## Three separate human activities and the actual schema

### 1. Claim provenance adjudication

Current supported records live at `explanations[].provenance_adjudications[claim_key]`. `scripts/adjudicate.py:record` writes:

```json
{
  "version": 1,
  "field": "<existing field>",
  "sentence": "<final exact sentence>",
  "decision": "<accepted | rejected | edited>",
  "rationale": "<actual reasoning, source location and relevant qualifications>",
  "adjudicated_by": "<real project-author reviewer name>",
  "adjudicated_at": "<actual review time in ISO 8601 with timezone>",
  "note": "provenance adjudication by the project author; NOT clinical approval"
}
```

These placeholders are documentation, not records. `claim_id` and `decision_scope` are supported optional fields for grouped decisions; no grouped decision is requested or inferred here. Leave a template decision null if no decision has actually been made. Accepted means the reviewer assessed the claim against its applicable source, including causal direction, limits and context. Rejected text still in the store blocks release. Edited requires review of the final replacement, with a newly computed key; it cannot approve a proposal in advance.

The template envelope supplies entry ID, claim key, exact sentence hash and current content/source/context hashes. It also has `reviewer_role`, `reviewed_source`, `reviewed_source_span` and `final_bytes_attestation`. These are **handoff evidence fields**, requested to document what was actually reviewed; they are not additional supported fields or automatically enforced requirements of the current adjudication record schema. The production schema has no separate role, source-reference or attestation field. Include the source location and relevant qualifications in the actual rationale as well. No cryptographic signature requirement is invented.

Preserve the 124 current records and two obsolete records. Reassess any flagged claim that is substantively unsupported, and do not silently apply an old decision to changed wording or a new source/context. The reviewer can confirm unchanged content in the exact-entry handoff without falsely rewriting historical timestamps.

### 2. Whole-entry author reading

Current supported fields are `review.read_by_author` and `review.read_at`. `scripts/author_read.py:_mark_read` records a name and actual UTC timestamp. This is a record that a person read the entry, **not clinical approval**. Do not set `provenance_verified` by hand: it is a machine-verification field with its own provenance.

For each of the 20 entries, read the final four explanation fields together with the source and semantic context. Return the template's `review_patch` only after that read, with the exact entry bindings in the enclosing handoff. If a proposed revision is selected, obtain a new packet or recomputed final bindings before attesting. No existing entry has an author-read record.

Implementation nuance: `review_status.py` reports author-read coverage separately, and its successful exit reflects machine provenance. `build_explanation_approvals.py` and `release_status.py` do not separately test `read_by_author` as a Boolean prerequisite. This task follows the requested complete-entry human handoff and does not alter the gate or silently treat its current exit logic as proof that entries were read. Any enforcement change is separate implementation work; none is made here.

### 3. Clinical expert review

The declared bounded research policy records **NOT_OBTAINED** and requires that no unsupported clinical-expert claim be made. It does not currently make a real clinician's approval a prerequisite for this bounded release. This is not permission to make clinical-readiness claims. The mapping file also warns that clinical claims require faculty review; this packet supplies no such sign-off.

The template's separate clinical section stays NOT_OBTAINED. A future actual expert review would need evidence of the real reviewer's appropriate qualifications, precise reviewed scope/content/source/context, actual findings and review time. Those are documentary prerequisites for an honest expert-review claim, not a newly implemented schema. Existing tooling deliberately does not provide a clinical-approval import path, and the current gate rejects an unsupported change to this status. Any future policy/schema integration needs its own explicit authorization.

## Important review questions

- **Safety/effectiveness overreach:** azathioprine NM, clopidogrel NM/URM and fluorouracil NM contain broad assurances; some carry historical bulk decisions. Primary sources do not turn normal PGx function into general safety or guaranteed response.
- **Thiopurine attribution/mechanism:** PMID 41618934 is Maillard et al., while the stored citation says Relling et al. TPMT and NUDT15 act differently; assess combined-gene applicability. The IM entry also retains legacy `Safe` context alongside reduced-dose source wording.
- **Clopidogrel context:** distinguish ACS/PCI, other cardiovascular and neurovascular source rows, and preserve contraindication conditions. The packet does not infer the user's indication.
- **Fixed patient facts:** stored non-Unknown rationale fields assert no non-reference variants. No patient-specific evidence in this packet establishes those statements. Runtime reconstruction does not waive stored-content review.
- **Version limits:** the DPYD source includes a 2017 paper and later recommendation updates. The official 2026 notice concerns a pending change; do not treat that notice as a completed bundle upgrade or hand-edit definitions.
- **Explicit abstention:** codeine and warfarin remain reviewed stored Unknown entries even though capability policy withholds guidance. No calling or dosing expansion is proposed.

## Returning decisions and later integration

Return a completed copy of the template, with decisions only for items actually reviewed. The 55 pending rows need decisions; the remaining rows are present to preserve context and allow a reviewer to flag/reassess existing bulk decisions. Return 20 genuine author-read records after final wording/source/context is settled. No blank, example, test fixture, automated result or this packet's draft is a human decision.

There is **no JSON response-envelope importer** in the current repository. An authorized maintainer must check each returned sentence/key/hash against the then-current bytes, preserve historical records, and integrate only the genuine supported-schema decisions. The envelope is not an approval manifest and must never be installed as one. If anything changed, stop integration of that item and request review of the new exact bytes.

The default adjudication walker skips already-decided automated records; `--escalated-only` covers the 19, not all 55. A human using the existing CLI must deliberately revisit automated decisions (`--redo` with an appropriate selection), while avoiding accidental replacement of unrelated records. `--all --redo` re-asks all selected sentences. No such writing command was run in this task.

After authorized text/decision integration, rerun provenance and appropriate regressions; deliberately invalidate obsolete content/source/context approvals, rebuild manifests only in a separately authorized step, and run the authoritative release gate against the final dirty-tree candidate. Source/context changes can require reassessment even when a normalized sentence key stays unchanged. A generated manifest must never retroactively imply a historical source attestation.

Default policy remains `human_review_all_stored_generated_entries`. Deterministic fallback does not waive the work. A template-only release would be a separate explicitly authorized policy decision with real review of the applicable fallback content. No entries were excluded, no empty set was declared reviewed, and no policy or manifest was changed here.

**Stop point:** real owner/reviewer action. F1 cannot be closed by this task.
