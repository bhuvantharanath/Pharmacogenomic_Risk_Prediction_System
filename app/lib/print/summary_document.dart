/// The printable one-page summary — the artifact a person hands over.
///
/// WHY THIS FILE IS A SAFETY SURFACE, NOT A STYLING ONE
///
/// The app cannot change a prescription. A person has to. So the only path from
/// this system to an actual clinical decision runs through a printed page that
/// leaves the app and is read by someone who never saw the screen it came from,
/// with none of the surrounding context and no way to ask a follow-up question.
///
/// Everything that page implies, it implies unsupervised. That governs two
/// decisions here, and both cut against making it look good.
///
/// **It must not look like a laboratory report.** No letterhead, no logo block,
/// no signature line, no seal, no accession number, no "Authorised by". Those
/// conventions are how a reader decides, in about a second and without reading
/// a word, whether a page carries clinical authority. This page does not. It is
/// a printout from a student research tool that no clinician has reviewed, and
/// it should look exactly like one — plain, dense, obviously a working document.
/// A handsome page here would be a lie told in typography.
///
/// **It must carry the negatives.** The disclaimer repeats on every page,
/// because pages get separated. The coverage census shows what was NOT checked,
/// not only what was — a reader who sees four confident results and no census
/// has no way to know that three genes were never resolved. Every Unknown is
/// listed with its own reason, and none is dropped to make the page tidier: the
/// Unknowns are frequently the most important thing on it, and a page that
/// prints only the confident rows would misrepresent the analysis by omission.
///
/// WHY HTML
///
/// It is a pure string, so the whole document is assertable in a unit test —
/// the disclaimer, the coverage figures and every Unknown reason are checked as
/// text rather than as pixels, which is the only way to verify a page nobody
/// will look at until it is already in someone else's hands.
///
/// One document, two renderers: the browser prints this HTML directly, and on
/// iOS and Android `printing` hands it to the OS renderer to make a PDF. Both
/// start from this string, so the printed page cannot drift from the shared
/// one. See `print_summary.dart`.
library;

import '../models/analysis.dart';
import '../models/enums.dart';
import '../models/unknown_reason.dart';
import '../widgets/summary_grid.dart';

/// Escapes text for HTML. CPIC's text is quoted verbatim, and verbatim means
/// verbatim — an ampersand in a guideline must not become an entity, and a
/// stray `<` must not silently eat the rest of the sentence.
String esc(String raw) => raw
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;');

/// The header that repeats on every printed page.
///
/// Not a banner to be styled around — it is the single most important sentence
/// on the sheet, and it is first because a reader who stops after one line must
/// still have read it.
const String kPrintHeaderLine =
    'RESEARCH AND EDUCATIONAL USE ONLY — NOT A MEDICAL DEVICE';

/// Build the whole document. Pure: same response in, same string out.
String buildSummaryHtml(AnalyzeResponse response, {DateTime? printedAt}) {
  final QualityMetrics m = response.qualityMetrics;
  final List<PerDrugResult> ordered = orderByConsequence(response.analyses);
  final List<PerDrugResult> unknowns = ordered
      .where((PerDrugResult r) => r.riskAssessment.riskLabel == RiskLabel.unknown)
      .toList();

  final StringBuffer b = StringBuffer();
  b.writeln('<!doctype html><html lang="en"><head>');
  b.writeln('<meta charset="utf-8">');
  b.writeln('<meta name="viewport" content="width=device-width,initial-scale=1">');
  b.writeln('<title>PharmaGuard summary — ${esc(response.patientId)}</title>');
  b.writeln('<style>${_css()}</style>');
  b.writeln('</head><body>');

  // A table `thead`, not `position: fixed`.
  //
  // Both repeat a header across printed pages in a desktop browser, but this
  // document is also converted to PDF by the OS renderer on iOS and Android,
  // and those do not reliably honour fixed positioning in paged media. A
  // repeated `thead` is the one mechanism every print engine implements. Since
  // "the disclaimer appears on every page" is a safety requirement rather than
  // a layout preference, it uses the mechanism that cannot quietly fail.
  b.writeln('<table class="page"><thead><tr><th>');
  b.writeln('<div class="running">$kPrintHeaderLine</div>');
  b.writeln('</th></tr></thead><tbody><tr><td>');

  b.writeln('<main>');
  // Stated once more as a block at the top of the document. The running header
  // is a thin repeated line; this is the one a reader actually stops on.
  b.writeln('<div class="banner">$kPrintHeaderLine</div>');
  b.writeln(_intro(response, printedAt));
  b.writeln(_disclaimer());
  b.writeln(_results(ordered));
  b.writeln(_unknownSection(unknowns, m));
  b.writeln(_census(m));
  b.writeln(_provenance(m));
  b.writeln('</main>');
  b.writeln('</td></tr></tbody></table>');
  b.writeln('</body></html>');
  return b.toString();
}

String _intro(AnalyzeResponse response, DateTime? printedAt) {
  final DateTime when = (printedAt ?? DateTime.now()).toUtc();
  final String stamp = '${when.year.toString().padLeft(4, '0')}-'
      '${when.month.toString().padLeft(2, '0')}-'
      '${when.day.toString().padLeft(2, '0')}';
  return '''
<h1>Pharmacogenomic analysis summary</h1>
<table class="kv">
  <tr><td>sample</td><td class="mono">${esc(response.patientId)}</td></tr>
  <tr><td>analysed</td><td class="mono">${esc(response.timestamp)}</td></tr>
  <tr><td>printed</td><td class="mono">$stamp</td></tr>
  <tr><td>drugs checked</td><td class="mono">${response.analyses.length}</td></tr>
</table>''';
}

String _disclaimer() => '''
<section class="warn">
  <p><strong>This is not a clinical report.</strong> It was produced by a
  final-year student project for research and education. It has not been
  clinically validated, and no qualified clinical expert has reviewed the
  explanatory text on this page.</p>
  <p>Every clinical statement here is machine-checked to trace back to a
  published CPIC recommendation. That verifies nothing was invented. It does not
  verify that any of it is correct for the person this sample came from.</p>
  <p>Do not change a medicine on the strength of this page. Take it to a
  qualified healthcare professional.</p>
</section>''';

String _results(List<PerDrugResult> ordered) {
  final StringBuffer b = StringBuffer()
    ..writeln('<h2>Results</h2>')
    ..writeln('<p class="note">Ordered by consequence, not alphabetically.</p>');

  for (final PerDrugResult r in ordered) {
    final PharmacogenomicProfile p = r.pharmacogenomicProfile;
    final ClinicalRecommendation c = r.clinicalRecommendation;
    b.writeln('<article class="result">');
    b.writeln('<div class="head">'
        '<span class="drug mono">${esc(r.drug)}</span>'
        '<span class="verdict">${esc(r.riskAssessment.riskLabel.wireValue)}'
        '</span></div>');
    b.writeln('<table class="kv">'
        '<tr><td>gene</td><td class="mono">${esc(p.primaryGene)}</td></tr>'
        '<tr><td>diplotype</td><td class="mono">${esc(p.diplotype)}</td></tr>'
        '<tr><td>phenotype</td><td class="mono">'
        '${esc(p.phenotype.wireValue)}</td></tr>'
        '<tr><td>evidence level</td><td class="mono">'
        '${esc(c.cpicEvidenceLevel.wireValue)}</td></tr>'
        '<tr><td>severity</td><td class="mono">'
        '${esc(r.riskAssessment.severity.wireValue)}</td></tr>'
        '</table>');

    if (r.llmGeneratedExplanation.summary.isNotEmpty) {
      b.writeln('<p class="prose">${esc(r.llmGeneratedExplanation.summary)}</p>');
    }

    // The quotation, with its attribution attached to it rather than to the
    // page. A quoted paragraph that travels without its source stops being a
    // quotation and starts being this project's own clinical claim.
    b.writeln('<div class="quote">');
    b.writeln('<div class="qlabel">CPIC GUIDELINE — QUOTED EXACTLY</div>');
    b.writeln('<p class="mono">${esc(c.action)}</p>');
    if (c.cpicRecommendation.isNotEmpty && c.cpicRecommendation != 'STUB') {
      b.writeln('<p class="mono small">${esc(c.cpicRecommendation)}</p>');
    }
    b.writeln('<p class="attrib mono">— ${esc(c.source)}</p>');
    b.writeln('</div>');
    b.writeln('</article>');
  }
  return b.toString();
}

/// Every Unknown, each with the reason it is Unknown.
///
/// Kept as its own section as well as appearing in the results above, because
/// this is the part a reader skims past. An Unknown is not a blank — it is the
/// system declining to assert something it cannot support, and which of the
/// four reasons applies determines whether the reader can do anything about it.
String _unknownSection(List<PerDrugResult> unknowns, QualityMetrics m) {
  if (unknowns.isEmpty) {
    return '<h2>Unknown results</h2>'
        '<p class="note">None — every drug checked returned a result.</p>';
  }

  final StringBuffer b = StringBuffer()
    ..writeln('<h2>Unknown results (${unknowns.length})</h2>')
    ..writeln('<p class="note">An Unknown is a declined answer, not a missing '
        'one. Only one of these reasons is something the sample provider can '
        'act on.</p>');

  for (final PerDrugResult r in unknowns) {
    final UnknownReason reason = classifyUnknown(r, m);
    b.writeln('<article class="unknown">');
    b.writeln('<div class="head">'
        '<span class="drug mono">${esc(r.drug)}</span>'
        '<span class="verdict">${esc(reason.headline)}</span></div>');
    b.writeln('<p class="prose">${esc(reason.explanation)}</p>');
    final String? action = reason.callToAction;
    if (action != null) {
      b.writeln('<p class="prose"><strong>What would fix it:</strong> '
          '${esc(action)}</p>');
    } else {
      b.writeln('<p class="note">Nothing about the uploaded file would change '
          'this result.</p>');
    }
    b.writeln('</article>');
  }
  return b.toString();
}

/// What was checked, and — the point — what was not.
String _census(QualityMetrics m) {
  if (m.positionCoverage.isEmpty) {
    return '<h2>Input coverage</h2>'
        '<p class="note">No per-gene coverage was reported for this run.</p>';
  }

  final List<String> genes = m.positionCoverage.keys.toList()..sort();
  final StringBuffer b = StringBuffer()
    ..writeln('<h2>Input coverage</h2>')
    ..writeln('<p class="note">How many of the positions each gene needs '
        'carried an explicit genotype in the uploaded file. A position that is '
        'absent reads as matching the reference, so missing data produces '
        'confident results rather than uncertain ones — which is why the count '
        'is printed whether or not it passed.</p>')
    ..writeln('<table class="census"><thead><tr>'
        '<th>gene</th><th>reported</th><th>required</th><th>minimum</th>'
        '<th>sufficient</th></tr></thead><tbody>');

  for (final String gene in genes) {
    final GeneCoverage c = m.positionCoverage[gene]!;
    b.writeln('<tr>'
        '<td class="mono">${esc(gene)}</td>'
        '<td class="mono">${c.positionsPresent}</td>'
        '<td class="mono">${c.positionsRequired}</td>'
        '<td class="mono">${c.minimumPercent}%</td>'
        '<td class="mono">${c.sufficient ? 'yes' : 'NO'}</td>'
        '</tr>');
  }
  b.writeln('</tbody></table>');

  final Iterable<String> short = genes.where(
      (String g) => !m.positionCoverage[g]!.sufficient);
  if (short.isNotEmpty) {
    b.writeln('<p class="note"><strong>Not resolved from this file:</strong> '
        '${esc(short.join(', '))}. Any drug keyed to these genes was reported '
        'as Unknown rather than assumed normal.</p>');
  }
  return b.toString();
}

String _provenance(QualityMetrics m) {
  final GuidelineProvenance? g = m.guidelineProvenance;
  if (g == null) return '';
  return '''
<h2>Where this guidance came from</h2>
<table class="kv">
  <tr><td>PharmCAT</td><td class="mono">${esc(g.pharmcatVersion)}</td></tr>
  ${g.cpicDataVersion.isEmpty ? '' : '<tr><td>CPIC data version</td>'
      '<td class="mono">${esc(g.cpicDataVersion)}</td></tr>'}
  <tr><td>explanations generated</td>
      <td class="mono">${esc(g.explanationsDate)}</td></tr>
  <tr><td>source</td><td class="mono">${esc(g.cpicSource)}</td></tr>
</table>
<p class="note">${esc(g.note)}</p>''';
}

/// Print styling. Deliberately plain.
///
/// One typeface family for prose and one monospace for machine output, black on
/// white, hairline rules. No colour fills, no logo space, no header band, no
/// signature block. Everything here exists to make the page legible; nothing
/// here exists to make it look official.
String _css() => '''
@page { margin: 14mm 12mm 12mm; }
* { box-sizing: border-box; }
body {
  margin: 0; padding: 0;
  font: 10.5pt/1.45 Georgia, 'Times New Roman', serif;
  color: #000; background: #fff;
}
.mono { font-family: 'IBM Plex Mono', Menlo, Consolas, monospace; }

/* The repeated header. A thead row is reprinted on every page by every print
   engine, including the OS HTML-to-PDF renderers on iOS and Android. */
table.page { width: 100%; border-collapse: collapse; }
table.page > thead { display: table-header-group; }
table.page > tbody { display: table-row-group; }
table.page > thead > tr > th, table.page > tbody > tr > td {
  padding: 0; text-align: left; font-weight: 400;
}
.running {
  font-family: 'IBM Plex Mono', Menlo, Consolas, monospace;
  font-size: 7.5pt; letter-spacing: 0.06em;
  padding-bottom: 3pt; margin-bottom: 10pt;
  border-bottom: 0.5pt solid #000;
}
@media screen {
  main { padding: 0 16px 48px; max-width: 800px; margin: 0 auto; }
  .running { padding: 8px 16px 4px; }
}

.banner {
  font-family: 'IBM Plex Mono', Menlo, Consolas, monospace;
  font-size: 8.5pt; letter-spacing: 0.06em; font-weight: 700;
  border: 1pt solid #000; padding: 5pt 7pt; margin: 0 0 10pt;
}
h1 { font-size: 15pt; margin: 0 0 8pt; font-weight: 600; }
h2 {
  font-size: 11pt; margin: 16pt 0 5pt; font-weight: 600;
  border-bottom: 0.5pt solid #000; padding-bottom: 2pt;
}
p { margin: 0 0 6pt; }
.note { font-size: 9pt; color: #333; }
.small { font-size: 9pt; }
.prose { max-width: 46em; }

.warn { border: 0.5pt solid #000; padding: 7pt 9pt; margin: 8pt 0 4pt; }
.warn p { font-size: 9.5pt; }

table.kv { border-collapse: collapse; margin: 0 0 7pt; }
table.kv td { padding: 1pt 12pt 1pt 0; vertical-align: top; font-size: 9.5pt; }
table.kv td:first-child { color: #333; width: 12em; }

article.result, article.unknown {
  border-top: 0.5pt solid #000; padding: 7pt 0 9pt;
  /* Never split a drug's result across a page break: half a recommendation is
     worse than a page with white space at the bottom. */
  break-inside: avoid; page-break-inside: avoid;
}
.head { display: flex; gap: 10pt; align-items: baseline; margin-bottom: 5pt; }
.drug { font-size: 9pt; letter-spacing: 0.05em; }
.verdict { font-size: 13pt; font-weight: 600; }

.quote { border: 0.5pt solid #666; padding: 6pt 8pt; margin: 6pt 0 0; }
.qlabel {
  font-family: 'IBM Plex Mono', Menlo, Consolas, monospace;
  font-size: 7.5pt; letter-spacing: 0.06em; color: #333; margin-bottom: 4pt;
}
.quote p { font-size: 9.5pt; margin-bottom: 4pt; }
.attrib { font-size: 8.5pt; color: #333; margin: 0; }

table.census { border-collapse: collapse; width: 100%; margin: 4pt 0 6pt; }
table.census th, table.census td {
  border-bottom: 0.5pt solid #999; padding: 2pt 6pt 2pt 0;
  text-align: left; font-size: 9pt;
}
table.census th {
  font-family: 'IBM Plex Mono', Menlo, Consolas, monospace;
  font-size: 7.5pt; letter-spacing: 0.05em; border-bottom-width: 1pt;
}
''';
