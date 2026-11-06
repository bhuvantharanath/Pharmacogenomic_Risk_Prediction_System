/// The printable summary as a PDF file — the same page, for a browser that can
/// only offer a print dialog and a reader who wants a file.
///
/// ONE PAGE, TWO RENDERERS, AND A TEST BETWEEN THEM
///
/// `summary_document.dart` explains why the summary is one HTML document: a
/// second layout of a safety-critical page can drop a disclaimer or an Unknown
/// reason while every test of the first stays green. This file IS a second
/// layout, so it does not rely on care to stay in step. It places exactly the
/// HTML document's text, node for node and in the same order, and every string
/// it places goes through [PdfTextSink]. A test compares that sequence with the
/// HTML's text nodes for every fixture response, so a sentence added to or
/// dropped from either document fails the build.
///
/// The disclaimer header repeats on every page, as the HTML's `thead` does.
library;

import 'dart:typed_data';

import 'package:flutter/services.dart' show rootBundle;
import 'package:pdf/pdf.dart';
import 'package:pdf/widgets.dart' as pw;

import '../models/analysis.dart';
import '../models/enums.dart';
import '../models/unknown_reason.dart';
import '../widgets/summary_grid.dart';
import 'summary_document.dart';

const String kPdfMediaType = 'application/pdf';

/// Which face a string is drawn in.
enum PdfFontRole { prose, mono, bold }

/// Receives every string the PDF places, in placement order.
typedef PdfTextSink = void Function(String text, PdfFontRole role);

/// The app's own fonts, so the PDF needs nothing the bundle does not carry.
///
/// All static IBM Plex Mono, prose included. The `pdf` package draws words
/// without space glyphs and leaves a reader to infer the gaps. With the app's
/// variable fonts (Newsreader, Public Sans), pypdf read the prose back as
/// "drugschecked" — a text layer that copy-paste and screen readers get wrong
/// (audit/phase9/B9.log). A test keeps every font here static.
class SummaryPdfFonts {
  const SummaryPdfFonts({
    required this.prose,
    required this.mono,
    required this.bold,
  });

  final pw.Font prose;
  final pw.Font mono;
  final pw.Font bold;

  static const Map<PdfFontRole, String> assets = <PdfFontRole, String>{
    PdfFontRole.prose: 'assets/fonts/IBMPlexMono-Regular.ttf',
    PdfFontRole.mono: 'assets/fonts/IBMPlexMono-Regular.ttf',
    PdfFontRole.bold: 'assets/fonts/IBMPlexMono-SemiBold.ttf',
  };

  static Future<SummaryPdfFonts> load() async {
    Future<pw.Font> font(PdfFontRole role) async =>
        pw.Font.ttf(await rootBundle.load(assets[role]!));
    return SummaryPdfFonts(
      prose: await font(PdfFontRole.prose),
      mono: await font(PdfFontRole.mono),
      bold: await font(PdfFontRole.bold),
    );
  }

  pw.Font of(PdfFontRole role) => switch (role) {
    PdfFontRole.prose => prose,
    PdfFontRole.mono => mono,
    PdfFontRole.bold => bold,
  };
}

/// Build the PDF. Same response, same `printedAt`, same text as
/// [buildSummaryHtml]. [onHeader] is told each page the running header is
/// drawn on, and [onPageCount] how many pages there are in the end.
Future<Uint8List> buildSummaryPdf(
  AnalyzeResponse response, {
  required SummaryPdfFonts fonts,
  DateTime? printedAt,
  PdfTextSink? sink,
  void Function(int page)? onHeader,
  void Function(int count)? onPageCount,
}) async {
  final _Page p = _Page(fonts, sink, onHeader);
  final QualityMetrics m = response.qualityMetrics;
  final List<PerDrugResult> ordered = orderByConsequence(response.analyses);
  final List<PerDrugResult> unknowns = ordered
      .where(
        (PerDrugResult r) => r.riskAssessment.riskLabel == RiskLabel.unknown,
      )
      .toList();

  final pw.Document doc = pw.Document(
    title: 'PharmaGuard summary — ${response.patientId}',
    creator: 'PharmaGuard (research and educational use only)',
  );
  doc.addPage(
    pw.MultiPage(
      pageFormat: PdfPageFormat.a4,
      margin: const pw.EdgeInsets.fromLTRB(34, 40, 34, 34),
      header: (pw.Context context) => p.runningHeader(context.pageNumber),
      build: (pw.Context context) => <pw.Widget>[
        p.banner(),
        ..._intro(p, response, printedAt),
        _disclaimer(p),
        ..._results(p, ordered),
        ..._unknownSection(p, unknowns, m),
        ..._census(p, m),
        ..._provenance(p, m),
      ],
    ),
  );
  final Uint8List bytes = await doc.save();
  onPageCount?.call(doc.document.pdfPageList.pages.length);
  return bytes;
}

List<pw.Widget> _intro(_Page p, AnalyzeResponse response, DateTime? at) {
  final DateTime when = (at ?? DateTime.now()).toUtc();
  final String stamp =
      '${when.year.toString().padLeft(4, '0')}-'
      '${when.month.toString().padLeft(2, '0')}-'
      '${when.day.toString().padLeft(2, '0')}';
  return <pw.Widget>[
    p.heading('Pharmacogenomic analysis summary', size: 15),
    p.keyValues(<(String, String)>[
      ('sample', response.patientId),
      ('analysed', response.timestamp),
      ('printed', stamp),
      ('drugs checked', '${response.analyses.length}'),
    ]),
  ];
}

pw.Widget _disclaimer(_Page p) => p.box(<pw.Widget>[
  p.leadIn(
    'This is not a clinical report.',
    'It was produced by a final-year student project for research and '
        'education. It has not been clinically validated, and no qualified '
        'clinical expert has reviewed the explanatory text on this page.',
  ),
  p.paragraph(
    'Recommendation text on this page is quoted from published CPIC guidance '
    'via PharmCAT. Automated source checks are not human review: they cannot '
    'show that every statement here is supported, or that any of it is '
    'correct for the person this sample came from.',
  ),
  p.paragraph(
    'Do not change a medicine on the strength of this page. Take it to a '
    'qualified healthcare professional.',
  ),
]);

List<pw.Widget> _results(_Page p, List<PerDrugResult> ordered) => <pw.Widget>[
  p.heading('Results'),
  p.note('Ordered by consequence, not alphabetically.'),
  for (final PerDrugResult r in ordered) _result(p, r),
];

pw.Widget _result(_Page p, PerDrugResult r) {
  final PharmacogenomicProfile profile = r.pharmacogenomicProfile;
  final ClinicalRecommendation c = r.clinicalRecommendation;
  return p.article(<pw.Widget>[
    p.head(r.drug, r.riskAssessment.riskLabel.wireValue),
    p.keyValues(<(String, String)>[
      ('gene', profile.primaryGene),
      ('diplotype', profile.diplotype),
      ('phenotype', profile.phenotype.wireValue),
      ('evidence level', c.cpicEvidenceLevel.wireValue),
    ]),
    if (profile.provenanceLine != null) p.note(profile.provenanceLine!),
    if (r.llmGeneratedExplanation.summary.isNotEmpty)
      p.paragraph(r.llmGeneratedExplanation.summary),
    // The quotation keeps its attribution, as on the HTML page.
    p.quote(<pw.Widget>[
      p.label(
        c.hasMatchedCpicEntry
            ? 'CPIC GUIDELINE — QUOTED EXACTLY'
            : 'APPLICATION LIMITATION — NOT A CPIC QUOTE',
      ),
      p.mono(c.action),
      if (c.cpicRecommendation.isNotEmpty && c.cpicRecommendation != 'STUB')
        p.mono(c.cpicRecommendation, size: 8.5),
      p.mono('— ${c.source}', size: 8),
    ]),
  ]);
}

List<pw.Widget> _unknownSection(
  _Page p,
  List<PerDrugResult> unknowns,
  QualityMetrics m,
) {
  if (unknowns.isEmpty) {
    return <pw.Widget>[
      p.heading('Unknown results'),
      p.note('None — every drug checked returned a result.'),
    ];
  }
  return <pw.Widget>[
    p.heading('Unknown results (${unknowns.length})'),
    p.note(
      'An Unknown is a declined answer, not a missing one. Only the reasons '
      'about the file itself — missing positions or unusable genotypes — are '
      'something the sample provider can act on.',
    ),
    if (unknowns.any(
      (PerDrugResult r) =>
          classifyUnknown(r, m) == UnknownReason.suppliedNotInterpretable,
    ))
      p.note(
        'A CYP2D6 call supplied with the file is an input too, and can be corrected.',
      ),
    for (final PerDrugResult r in unknowns) _unknown(p, r, m),
  ];
}

pw.Widget _unknown(_Page p, PerDrugResult r, QualityMetrics m) {
  final UnknownReason reason = classifyUnknown(r, m);
  final String? action = reason.callToAction;
  return p.article(<pw.Widget>[
    p.head(r.drug, reason.headline),
    p.paragraph(unknownExplanation(r, reason)),
    if (action != null)
      p.leadIn('What would fix it:', action)
    else
      p.note('Nothing about the uploaded file would change this result.'),
  ]);
}

List<pw.Widget> _census(_Page p, QualityMetrics m) {
  if (m.positionCoverage.isEmpty) {
    return <pw.Widget>[
      p.heading('Input coverage'),
      p.note('No per-gene coverage was reported for this run.'),
    ];
  }
  final List<String> genes = m.positionCoverage.keys.toList()..sort();
  final List<String> short = <String>[
    for (final String g in genes)
      if (!m.positionCoverage[g]!.sufficient) g,
  ];
  return <pw.Widget>[
    p.heading('Input coverage'),
    p.note(
      'How many of the positions each gene needs carried a usable genotype in '
      'the uploaded file. A genotype caller reads an absent position as '
      'matching the reference, so missing data can produce confident results '
      'rather than uncertain ones — which is why the count is printed whether '
      'or not it passed, and why a gene below its minimum is reported as '
      'Unknown.',
    ),
    p.table(
      <String>['gene', 'usable', 'required', 'minimum', 'sufficient'],
      <List<String>>[
        for (final String g in genes)
          <String>[
            g,
            '${m.positionCoverage[g]!.positionsPresent}',
            '${m.positionCoverage[g]!.positionsRequired}',
            '${m.positionCoverage[g]!.minimumPercent}%',
            m.positionCoverage[g]!.sufficient ? 'yes' : 'NO',
          ],
      ],
    ),
    if (short.isNotEmpty)
      p.leadIn(
        'Not resolved from this file:',
        '${short.join(', ')}. Any drug keyed to these genes was reported as '
            'Unknown rather than assumed normal.',
        note: true,
      ),
  ];
}

List<pw.Widget> _provenance(_Page p, QualityMetrics m) {
  final GuidelineProvenance? g = m.guidelineProvenance;
  if (g == null) return <pw.Widget>[];
  return <pw.Widget>[
    p.heading('Where this guidance came from'),
    p.keyValues(<(String, String)>[
      ('PharmCAT', g.pharmcatVersion),
      if (g.cpicDataVersion.isNotEmpty)
        ('CPIC data version', g.cpicDataVersion),
      if (g.cpicGuidanceSha256.isNotEmpty)
        ('CPIC table SHA-256', g.cpicGuidanceSha256),
      if (g.alleleDefinitionsVersion.isNotEmpty)
        ('allele definitions', g.alleleDefinitionsVersion),
      if (g.alleleDefinitionsSha256.isNotEmpty)
        ('definitions SHA-256', g.alleleDefinitionsSha256),
      if (g.pharmvarRelease.isNotEmpty) ('PharmVar release', g.pharmvarRelease),
      ('explanations generated', g.explanationsDate),
      ('source', g.cpicSource),
    ]),
    p.note(g.note),
  ];
}

/// The few kinds of element the page is made of. Every string passes through
/// [_text], which reports it to the sink before drawing it.
class _Page {
  _Page(this.fonts, this.sink, this.onHeader);

  final SummaryPdfFonts fonts;
  final PdfTextSink? sink;
  final void Function(int page)? onHeader;

  static const PdfColor _grey = PdfColor.fromInt(0xFF333333);
  static const PdfColor _rule = PdfColor.fromInt(0xFF666666);

  pw.TextStyle style(PdfFontRole role, double size, {PdfColor? color}) =>
      pw.TextStyle(
        font: fonts.of(role),
        fontSize: size,
        color: color ?? PdfColors.black,
        lineSpacing: 1.5,
      );

  pw.Widget _text(
    String text,
    PdfFontRole role,
    double size, {
    PdfColor? color,
  }) {
    sink?.call(text, role);
    return pw.Text(text, style: style(role, size, color: color));
  }

  /// Not reported to the sink: it is drawn once per page, so it reports the
  /// page instead, from the same place that draws its text.
  pw.Widget runningHeader(int page) {
    onHeader?.call(page);
    return pw.Container(
      padding: const pw.EdgeInsets.only(bottom: 3),
      margin: const pw.EdgeInsets.only(bottom: 10),
      decoration: const pw.BoxDecoration(
        border: pw.Border(bottom: pw.BorderSide(width: 0.5)),
      ),
      child: pw.Text(kPrintHeaderLine, style: style(PdfFontRole.mono, 7.5)),
    );
  }

  pw.Widget banner() => pw.Container(
    padding: const pw.EdgeInsets.symmetric(horizontal: 7, vertical: 5),
    margin: const pw.EdgeInsets.only(bottom: 10),
    decoration: pw.BoxDecoration(border: pw.Border.all(width: 1)),
    child: _text(kPrintHeaderLine, PdfFontRole.bold, 8.5),
  );

  pw.Widget heading(String text, {double size = 11}) => pw.Container(
    margin: pw.EdgeInsets.only(top: size > 11 ? 0 : 16, bottom: 6),
    padding: const pw.EdgeInsets.only(bottom: 2),
    decoration: size > 11
        ? null
        : const pw.BoxDecoration(
            border: pw.Border(bottom: pw.BorderSide(width: 0.5)),
          ),
    child: _text(text, PdfFontRole.bold, size),
  );

  pw.Widget paragraph(String text) => pw.Padding(
    padding: const pw.EdgeInsets.only(bottom: 6),
    child: _text(text, PdfFontRole.prose, 10),
  );

  pw.Widget note(String text) => pw.Padding(
    padding: const pw.EdgeInsets.only(bottom: 6),
    child: _text(text, PdfFontRole.prose, 9, color: _grey),
  );

  pw.Widget label(String text) => pw.Padding(
    padding: const pw.EdgeInsets.only(bottom: 4),
    child: _text(text, PdfFontRole.mono, 7.5, color: _grey),
  );

  pw.Widget mono(String text, {double size = 9.5}) => pw.Padding(
    padding: const pw.EdgeInsets.only(bottom: 4),
    child: _text(text, PdfFontRole.mono, size),
  );

  /// A bold lead-in followed by plain text in one paragraph, like the HTML's
  /// `<strong>…</strong> …`.
  pw.Widget leadIn(String lead, String rest, {bool note = false}) {
    sink?.call(lead, PdfFontRole.bold);
    sink?.call(rest, PdfFontRole.prose);
    final double size = note ? 9 : 10;
    return pw.Padding(
      padding: const pw.EdgeInsets.only(bottom: 6),
      child: pw.RichText(
        text: pw.TextSpan(
          children: <pw.InlineSpan>[
            pw.TextSpan(text: lead, style: style(PdfFontRole.bold, size)),
            pw.TextSpan(
              text: ' $rest',
              style: style(PdfFontRole.prose, size, color: note ? _grey : null),
            ),
          ],
        ),
      ),
    );
  }

  pw.Widget head(String drug, String verdict) => pw.Padding(
    padding: const pw.EdgeInsets.only(bottom: 5),
    child: pw.Row(
      crossAxisAlignment: pw.CrossAxisAlignment.end,
      children: <pw.Widget>[
        _text(drug, PdfFontRole.mono, 9),
        pw.SizedBox(width: 10),
        pw.Expanded(child: _text(verdict, PdfFontRole.bold, 13)),
      ],
    ),
  );

  pw.Widget keyValues(List<(String, String)> rows) => pw.Padding(
    padding: const pw.EdgeInsets.only(bottom: 7),
    child: pw.Table(
      columnWidths: const <int, pw.TableColumnWidth>{
        0: pw.FixedColumnWidth(110),
        1: pw.FlexColumnWidth(),
      },
      children: <pw.TableRow>[
        for (final (String key, String value) in rows)
          pw.TableRow(
            children: <pw.Widget>[
              pw.Padding(
                padding: const pw.EdgeInsets.only(right: 12, bottom: 1),
                child: _text(key, PdfFontRole.prose, 9.5, color: _grey),
              ),
              pw.Padding(
                padding: const pw.EdgeInsets.only(bottom: 1),
                child: _text(value, PdfFontRole.mono, 9),
              ),
            ],
          ),
      ],
    ),
  );

  pw.Widget table(List<String> header, List<List<String>> rows) => pw.Padding(
    padding: const pw.EdgeInsets.only(top: 4, bottom: 6),
    child: pw.Table(
      border: const pw.TableBorder(
        horizontalInside: pw.BorderSide(width: 0.5, color: _rule),
        bottom: pw.BorderSide(width: 0.5, color: _rule),
      ),
      children: <pw.TableRow>[
        pw.TableRow(
          children: <pw.Widget>[
            for (final String h in header) _cell(h, PdfFontRole.bold, 7.5),
          ],
        ),
        for (final List<String> row in rows)
          pw.TableRow(
            children: <pw.Widget>[
              for (final String v in row) _cell(v, PdfFontRole.mono, 9),
            ],
          ),
      ],
    ),
  );

  pw.Widget _cell(String text, PdfFontRole role, double size) => pw.Padding(
    padding: const pw.EdgeInsets.fromLTRB(0, 2, 6, 2),
    child: _text(text, role, size),
  );

  pw.Widget box(List<pw.Widget> children) => pw.Container(
    padding: const pw.EdgeInsets.fromLTRB(9, 7, 9, 2),
    margin: const pw.EdgeInsets.only(top: 8, bottom: 4),
    decoration: pw.BoxDecoration(border: pw.Border.all(width: 0.5)),
    child: pw.Column(
      crossAxisAlignment: pw.CrossAxisAlignment.start,
      children: children,
    ),
  );

  pw.Widget quote(List<pw.Widget> children) => pw.Container(
    padding: const pw.EdgeInsets.fromLTRB(8, 6, 8, 4),
    margin: const pw.EdgeInsets.only(top: 6),
    decoration: pw.BoxDecoration(
      border: pw.Border.all(width: 0.5, color: _rule),
    ),
    child: pw.Column(
      crossAxisAlignment: pw.CrossAxisAlignment.start,
      children: children,
    ),
  );

  /// One drug. Never split across a page break, as on the HTML page: half a
  /// recommendation is worse than white space at the foot of a page.
  pw.Widget article(List<pw.Widget> children) => pw.Container(
    padding: const pw.EdgeInsets.only(top: 7, bottom: 9),
    decoration: const pw.BoxDecoration(
      border: pw.Border(top: pw.BorderSide(width: 0.5)),
    ),
    child: pw.Column(
      crossAxisAlignment: pw.CrossAxisAlignment.start,
      children: children,
    ),
  );
}
