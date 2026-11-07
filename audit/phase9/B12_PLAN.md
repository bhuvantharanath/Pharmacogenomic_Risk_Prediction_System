# B12 — Accessibility fixes (from A8)

Part B item 12 of the Phase 9 brief:

> Fix every failing contrast pair, add semantic labels, make risk never
> colour-only (icon + text), support 200% text scale.

Written 2026-11-07 before any B12 code. Its sha256 goes into
`audit/phase9/B12.log` before the first edit. Nothing here is edited after
measurement.

## State at B11 (bcfe650, live)

A8 measured the **live client built from 0a8b129**, which predates B1–B11.
Re-measured against HEAD today, because the client changed in B8–B11 and A8's
line numbers are stale. The contrast arithmetic was re-implemented from the
WCAG 2.2 definition and reproduces every published A8 figure to two decimals
(`ink3`/paper 3.13, `ink3`/card 3.43, `accent`/paper 8.28, `rule` 1.36,
`rule2` 1.64, `accentRule` 1.96, `ink2`/paper 5.50, `adjust`/card 5.63), so the
two measurements are comparable.

**The app renders light only.** `main.dart:25` sets `theme:` and no
`darkTheme:`, so `MaterialApp` uses the light theme at either platform
brightness and the `Brightness.dark` branches in six widgets never execute.
Contrast is therefore assessed in light only, and that is a finding in itself,
not an omission.

### Genuinely failing, in use

| id | defect | measured |
|---|---|---|
| D1 | `ink3 #7D8A81` as **text** | 3.13 on paper, 3.43 on card — below AA 4.5. Three sites: `coverage_census.dart:125`, `file_readiness.dart:173`, `verdict_card.dart:281` |
| D2 | `rule #D3DACE` / `rule2 #BFC8BA` / `accentRule #C6ADC8` as the **only cue to an interactive control's extent** | 1.36 / 1.64 / 1.96 on card — below the 3.0 non-text minimum. Control boundaries: the file-readiness box (`file_readiness.dart:63`), the view toggle (`view_toggle.dart:27,82`), the grid card (`summary_grid.dart:145`), the verdict card (`verdict_card.dart:77`) |
| D3 | four **"Try this"** and four **"Download"** buttons share accessible names (`sample_files.dart:227,232`) | A8's finding, still true at HEAD |
| D4 | status and error messages are `SelectableText`, exposed as **unlabelled textboxes** (`error_panel.dart:67`, `home_screen.dart:821`, `backend_status_banner.dart:121`, `version_notice.dart:91`) | A8 saw one; there are four |
| D5 | **200% text scale overflows** at 360 px: 4 distinct `RenderFlex` overflows, up to 176 px, at `results_screen.dart:366`, `:461`, `:487`; 2 overflows already at 150%. At 1440 px, none at any scale | A8 had this "not measured"; measured today |

### Not defects — recorded so they are not "fixed" for show

- **`ink3` as an icon or underline colour** (`disclosure_row.dart:105`,
  `summary_grid.dart:175`, `glossary_text.dart:168`) is non-text: 3.13 and
  3.43 both clear the 3.0 minimum.
- **Every verdict text pair passes.** The colours actually used for verdict
  text come from `Tokens.verdict()`: safe/safeBg 5.82, adjust/adjustBg 4.96,
  danger/dangerBg 6.72, accent/accentBg 7.68.
- **Legend swatches pass** the 3.0 non-text minimum (4.08–6.54), and white on
  every badge is 4.69–6.54.
- **`RiskStyle.adjust` failing "as text"** in A8's table is not an in-use pair:
  at HEAD `RiskStyle` is read in exactly one place, the results-screen legend
  (`results_screen.dart:486`), where `accent` is a 10×10 swatch beside text in
  the ordinary ink colour. `RiskStyle.onContainer` and `.container` are unused.
- **Risk is already not colour-only**: every verdict shows its label as text,
  which satisfies WCAG 1.4.1 on its own.
- **The row's accessible name no longer carries "severity critical"** — that
  was the 0a8b129 build A8 examined; `summary_grid.dart:153` is now
  `'<drug>: <label>'`.

### Worth doing, and honest about why

- **I1 — Toxic and Ineffective share a colour and show no icon.** Both resolve
  to `danger`/`dangerBg` and the cards draw no risk icon, so at a glance the
  two most serious verdicts differ only by the word. `RiskStyle.icon` already
  distinguishes them (`warning_amber_rounded` vs `block`) and is currently
  used only in the legend. This is an improvement, not a WCAG failure, and is
  labelled as such.

## Design

1. **D1.** Darken `ink3` until it clears 4.5 on `paper`, the worse of the two
   backgrounds, keeping the hue. It stays one token: a second "ink3 for text"
   would be a trap for the next edit.
2. **D2.** Raise only the borders that bound an interactive control, by giving
   those sites a stronger token. Hairlines that merely separate rows are
   decorative and are left alone — WCAG 1.4.11 asks for 3:1 on what identifies
   a component, not on every line.
3. **D3.** `Text(..., semanticsLabel: ...)` on each button, naming its sample.
   The visible text is unchanged.
4. **D4.** Give each status and error message a `Semantics` node with a name,
   and mark the ones that appear in response to an action as live regions so a
   screen reader announces them.
5. **D5.** The three rows are `Row(mainAxisSize: min)` holding a `Text` that
   cannot shrink. Wrap the text in `Flexible`, the idiom `view_toggle.dart`
   already uses for the same reason.
6. **I1.** Draw `RiskStyle.icon` beside the verdict in the row and the panel.

## Acceptance criteria

| # | Criterion |
|---|---|
| AC1 | Contrast, by test: a test computes WCAG 2.2 ratios from the tokens and asserts every pair used as text is ≥ 4.5 and every pair used as an interactive control's boundary is ≥ 3.0. The pair list is asserted against the source, so a new use site that is not covered fails the test rather than passing silently. The same test reproduces A8's published figures for the tokens B12 does not change |
| AC2 | No ambiguous control names, by test: on the home screen with semantics enabled, every button's accessible name is unique, and each sample's two buttons name that sample |
| AC3 | Messages are named, by test: each status and error message exposes a non-empty accessible name and is not a bare textbox |
| AC4 | Risk never colour-only, by test: for every ordered pair of distinct `RiskLabel`s, the rendered verdict differs in its text **and** in its icon, not only in colour; in particular Toxic and Ineffective, which share a colour |
| AC5 | 200% text scale, by test: at 360 px and 1440 px, at scales 1.0, 1.5 and 2.0, opening every card on the results screen produces zero `RenderFlex` overflows. The test fails on overflow rather than printing it |
| AC6 | Suites and gate: full backend and Flutter suites pass, and the release gate is ready |

## Zero-regression

- **S1–S6, cohort, 74 PharmCAT VCFs, A4:** identical to B11 in labels and
  statuses, and S1–S6 bodies identical. No backend file is changed.
- **Exports:** the printable HTML summaries and FHIR bundles for all nine
  fixtures are byte-identical to B11's. Neither reads the colour tokens
  (`summary_document.dart` and `fhir_report.dart` import no theme), so a
  contrast change must not move them — and if it does, something reads the
  theme that should not.
- **External evaluation:** the re-bind shows no eligibility or discrepancy
  change against B11's package.

## Sabotage

Each must turn a test red, and the files are restored byte-identical
afterwards.

| id | sabotage |
|---|---|
| SB12-a | `ink3` is put back to its failing value |
| SB12-b | a control's boundary is put back to the low-contrast token |
| SB12-c | one sample's button loses its distinguishing semantic label |
| SB12-d | a status message loses its accessible name |
| SB12-e | Ineffective is given Toxic's icon, so the two differ by colour and word only |
| SB12-f | a `Flexible` is removed from one of the three rows, restoring the 200% overflow |

## After deploy (only if the owner approves a deploy)

Live criteria, to be logged before measuring:

- **Commit.** The Deploy run succeeds and `/ready` reports the commit.
- **S1–S6.** As at B11, and the served bodies equal B11's live bodies.
- **Bundle.** The production bundle carries the new token values.
- **Browser.** On the live page at 200% text scale and 360 px, no clipped text;
  the sample buttons' accessible names are distinct; a verdict shows its icon.

## Out of scope

- **A dark theme.** None is wired; adding one is a feature, not an
  accessibility fix, and would need its own contrast pass.
- **Keyboard focus order and TalkBack**, both "not measured" in A8 and needing
  a real device or a manual pass. B12 does not claim them.
- **The first-time-user findings** in A8 (warfarin's preview wording and the
  queue message), which are F-01/F-11/F-14 and belong to their own items.
- **Removing `RiskStyle.onContainer`/`.container` or the dead dark branches.**
  Noted, not swept into an accessibility item.
