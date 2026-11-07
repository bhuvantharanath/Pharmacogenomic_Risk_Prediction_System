# B12 — L4 amendment, by owner decision

Recorded 2026-11-07, after measurement, at the owner's explicit instruction ("Amend
L4"). The plan (`audit/phase9/B12_PLAN.md`, sha256 e3737625…) and the live criteria in
`audit/phase9/B12.log` (the log's sha256 was 4570341f… when they were written) are left
unedited, so their hashes still prove what was pre-committed.

## What happened

L4 was written as:

> The deployed web bundle (main.dart.js) carries EXPECTED_BACKEND_SHA bc5c396… and the
> three new token values 646E67, 848A80 and 968398. Its own negative control, needing
> no extra fetch: the superseded ink3 value 7D8A81 must be ABSENT, because the only
> reason it was in the bundle was the defect B12 fixed.

Measured, the commit check passed and all three token checks failed
(`partb/B12/live_bundle.json` before this amendment, kept as
`live_bundle.attempt1-wrong-encoding.json`).

## Why the clause did not fit

The criterion assumed Flutter compiles `Color(0xFF646E67)` into something containing the
text `646E67`. It does not. Probing the bundle for `rule` — a token B12 never touched,
which therefore **must** be present if the method works at all — found nothing either,
in any of: decimal, `0xFFRRGGBB`, `0xffrrggbb`, bare upper hex, bare lower hex. The whole
3.75 MB bundle contains **zero** `0xffRRGGBB`-shaped literals. Flutter's `Color` stores
its channels as doubles, and dart2js emits those.

So L4 as written could not have passed for a correct deployment, and the failure says
nothing about whether B12 shipped.

## The worse half: the negative control was vacuous

`7D8A81` reported ABSENT and therefore PASS. But no colour appears as a hex string, so
that check would have reported PASS whatever was deployed — including a bundle still
carrying the failing `ink3`. It was not weak evidence; it was no evidence, and it was
the half of L4 meant to prove the fix had actually shipped rather than merely that some
new string existed.

This is the part worth recording. A negative control that cannot fail is worse than no
control, because it reads in the log as if something was checked.

## The amended criterion

L4 is amended to measure the same fact in the encoding the compiler actually uses. A
colour is present when its **three channel literals co-occur** within 300 characters —
not when each appears somewhere, since `0.39215686` on its own is only "some channel
equal to 100".

The bundle must carry EXPECTED_BACKEND_SHA bc5c396…, and:

| probe | expected | why it is in the set |
|---|---|---|
| `rule` #D3DACE | present | unchanged by B12; if absent, the method is broken |
| `accent` #5A3A5F | present | second unchanged control |
| `ink3` #646E67 | present | the new value |
| `controlEdge` #848A80 | present | the new value |
| `accentControlEdge` #968398 | present | the new value |
| `ink3` old #7D8A81 | **absent** | the real negative control: it was in the bundle only because of the defect |
| #123456, never in the app | **absent** | proves the probe is not trivially true |
| `GenomeIndia`, `IndiGen` | absent | out of scope at B11 and still unimplemented |

Two positive controls and three negative ones, so the result discriminates in both
directions.

## Scope

This amends how L4 is measured. It does not change what B12 claims, weaken any other
criterion, or touch AC1–AC6, which were measured in the Flutter suite and are the
stronger evidence: `accessibility_test.dart` recomputes the ratios from the tokens and
fails the build, whereas L4 only confirms the right bytes reached the CDN.
