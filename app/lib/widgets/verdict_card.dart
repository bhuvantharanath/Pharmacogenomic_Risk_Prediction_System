/// One drug's result: verdict panel → coverage census → disclosure rows.
///
/// The verdict is a large serif word on a tinted panel, not a pill badge. A pill
/// reads as a tag applied to something; this is the finding itself, and it should
/// carry the weight of a headline.
///
/// `recommendation_diplotype` is NEVER rendered. It is PharmCAT's internal
/// reduction used to locate a CPIC row, and showing a patient two diplotypes
/// would move a parser-level confusion into the interface. It stays in the JSON
/// for auditors.
library;

import 'package:flutter/material.dart';

import '../glossary/glossary_text.dart';
import '../models/analysis.dart';
import '../models/enums.dart';
import '../models/unknown_reason.dart';
import '../theme/tokens.dart';
import 'coverage_census.dart';
import 'disclosure_row.dart';
import 'unknown_reason_panel.dart';
import 'view_mode.dart';

/// Genes that no VCF can resolve, with the reason shown in place of ticks.
const Map<String, String> _notCallableFromVcf = <String, String>{
  'CYP2D6': 'Defined by copy-number and structural variation, which a VCF '
      'cannot represent. A different kind of genetic test is required.',
};

class VerdictCard extends StatefulWidget {
  const VerdictCard({
    super.key,
    required this.result,
    required this.metrics,
    this.inGrid = false,
    this.mode = ViewMode.patient,
  });

  final PerDrugResult result;
  final QualityMetrics metrics;

  /// True when this card is opening inside a `SummaryGrid` row. The row already
  /// carries the drug, verdict and severity, so repeating them would say the
  /// same thing twice and push the actual detail further down the screen.
  final bool inGrid;

  /// Which register to render in. Reorders this card's body; changes nothing
  /// about what it contains. See `view_mode.dart`.
  final ViewMode mode;

  @override
  State<VerdictCard> createState() => _VerdictCardState();
}

class _VerdictCardState extends State<VerdictCard> {

  @override
  Widget build(BuildContext context) {
    final r = widget.result;
    final p = r.pharmacogenomicProfile;
    final (Color fg, Color bg) = Tokens.verdict(r.riskAssessment.riskLabel);
    final GeneCoverage? cov = widget.metrics.positionCoverage[p.primaryGene];
    final String? na = _notCallableFromVcf[p.primaryGene.toUpperCase()];

    return Container(
      margin: EdgeInsets.only(bottom: widget.inGrid ? 0 : 14),
      decoration: BoxDecoration(
        color: Tokens.card,
        borderRadius: Tokens.radiusLg,
        border: widget.inGrid
            ? null
            : Border.all(color: Tokens.rule, width: Tokens.hairline),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          if (!widget.inGrid) _verdictPanel(r, fg, bg),
          Padding(
            padding: const EdgeInsets.fromLTRB(14, 13, 14, 4),
            child: CoverageCensus(
              gene: p.primaryGene,
              coverage: cov,
              notApplicableReason: na,
            ),
          ),
          if (r.riskAssessment.riskLabel == RiskLabel.unknown)
            Padding(
              padding: const EdgeInsets.fromLTRB(14, 10, 14, 4),
              child: UnknownReasonPanel(
                reason: classifyUnknown(r, widget.metrics),
                profile: p,
                coverage: cov,
              ),
            ),
          const SizedBox(height: 8),
          // The census above and the disclaimer on the screen are outside this
          // switch on purpose: neither view may hide what was not checked.
          ...switch (widget.mode) {
            ViewMode.patient => _patientBody(r, p),
            ViewMode.clinician => _clinicianBody(r, p),
          },
        ],
      ),
    );
  }

  /// Prose surfaced; genotype and CPIC's own text one tap away.
  List<Widget> _patientBody(PerDrugResult r, PharmacogenomicProfile p) =>
      <Widget>[
        Padding(
          padding: const EdgeInsets.fromLTRB(14, 2, 14, 14),
          child: _prose(r),
        ),
        Container(height: Tokens.hairline, color: Tokens.rule),
        DisclosureRow(
            title: "The guideline in CPIC's own words", child: _cpicBody(r)),
        DisclosureRow(
            title: 'What was found in your file', child: _foundBody(p, r)),
      ];

  /// Genotype and guideline surfaced; the plain-language reading demoted.
  ///
  /// Demoted, not dropped. A clinician explaining a result to the person it is
  /// about needs the sentence that person will understand, and making them
  /// switch views to find it would put it out of reach at the moment it matters.
  List<Widget> _clinicianBody(PerDrugResult r, PharmacogenomicProfile p) =>
      <Widget>[
        Padding(
          padding: const EdgeInsets.fromLTRB(14, 2, 14, 12),
          child: _facts(p, r),
        ),
        Padding(
          padding: const EdgeInsets.fromLTRB(14, 0, 14, 14),
          child: _cpicBody(r),
        ),
        Container(height: Tokens.hairline, color: Tokens.rule),
        DisclosureRow(title: 'In plain language', child: _prose(r)),
        if (p.detectedVariants.isNotEmpty)
          DisclosureRow(
              title: 'Positions reported in your file', child: _variants(p)),
      ];

  Widget _verdictPanel(PerDrugResult r, Color fg, Color bg) {
    final sev = r.riskAssessment.severity;
    final bool critical = Tokens.severityRank(sev) >= 4;
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.fromLTRB(14, 13, 14, 13),
      decoration: BoxDecoration(
        color: bg,
        borderRadius: const BorderRadius.vertical(top: Radius.circular(6)),
        border: Border(
            bottom: BorderSide(color: Tokens.rule, width: Tokens.hairline)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          // Drug name in mono: it is the identifier the request carried.
          Text(r.drug.toLowerCase(), style: Tokens.monoLabel.copyWith(color: fg)),
          const SizedBox(height: 4),
          Text(r.riskAssessment.riskLabel.wireValue,
              style: Tokens.verdictText.copyWith(color: fg)),
          const SizedBox(height: 7),
          Wrap(
            spacing: 14,
            runSpacing: 4,
            children: <Widget>[
              // Severity is what separates Toxic from Ineffective — they share a
              // colour, so weight carries the rank.
              Text(
                'severity ${sev.wireValue}',
                style: Tokens.monoSm.copyWith(
                  color: critical ? fg : Tokens.ink2,
                  fontWeight: critical ? FontWeight.w600 : FontWeight.w400,
                ),
              ),
              Text(
                'confidence '
                '${(r.riskAssessment.confidenceScore * 100).round()}%',
                style: Tokens.monoSm,
              ),
            ],
          ),
        ],
      ),
    );
  }

  /// The prose. Serif, because it was written to be read by a person.
  Widget _prose(PerDrugResult r) => Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          GlossaryText(r.llmGeneratedExplanation.summary, style: Tokens.prose),
          if (r.llmGeneratedExplanation.mechanism.isNotEmpty) ...<Widget>[
            const SizedBox(height: 10),
            GlossaryText(r.llmGeneratedExplanation.mechanism,
                style: Tokens.proseSm),
          ],
        ],
      );

  /// CPIC's text, under a label that names it as quoted.
  ///
  /// `action` carries CPIC's DIRECTIVE ("Avoid clopidogrel if possible...").
  /// `cpic_recommendation` carries the surrounding metadata — strength,
  /// population, implications. The directive is what a reader needs first; an
  /// earlier version showed the metadata under this label, which quoted CPIC
  /// accurately but answered a question nobody asked.
  Widget _cpicBody(PerDrugResult r) => Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          Text('CPIC GUIDELINE — QUOTED EXACTLY', style: Tokens.monoLabel),
          const SizedBox(height: 6),
          Container(
            width: double.infinity,
            padding: const EdgeInsets.all(11),
            decoration: BoxDecoration(
              border: Border.all(color: Tokens.rule2, width: Tokens.hairline),
              borderRadius: Tokens.radius,
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: <Widget>[
                Text(r.clinicalRecommendation.action, style: Tokens.monoMd),
                if (r.clinicalRecommendation.cpicRecommendation.isNotEmpty &&
                    r.clinicalRecommendation.cpicRecommendation !=
                        'STUB') ...<Widget>[
                  const SizedBox(height: 9),
                  Container(height: Tokens.hairline, color: Tokens.rule),
                  const SizedBox(height: 9),
                  Text(r.clinicalRecommendation.cpicRecommendation,
                      style: Tokens.monoSm),
                ],
                const SizedBox(height: 9),
                // Attribution, always attached to the quote rather than to the
                // screen. A quoted paragraph that travels without its source —
                // into a screenshot, a printout — stops being a quotation.
                Text('— ${r.clinicalRecommendation.source}',
                    style: Tokens.monoSm.copyWith(color: Tokens.ink3)),
              ],
            ),
          ),
        ],
      );

  /// The genotype facts, in mono. Machine output, labelled as such.
  Widget _facts(PharmacogenomicProfile p, PerDrugResult r) {
    final rows = <(String, String)>[
      ('gene', p.primaryGene),
      ('diplotype', p.diplotype),
      ('phenotype', p.phenotype.wireValue),
      if (p.activityScore != null)
        ('activity score', p.activityScore!.toStringAsFixed(1)),
      ('evidence level', r.clinicalRecommendation.cpicEvidenceLevel.wireValue),
      ('variants reported', '${p.detectedVariants.length}'),
    ];
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: <Widget>[
        for (final (String k, String v) in rows)
          Padding(
            padding: const EdgeInsets.only(bottom: 5),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: <Widget>[
                SizedBox(
                    width: 116, child: GlossaryText(k, style: Tokens.monoSm)),
                Expanded(child: Text(v, style: Tokens.monoMd)),
              ],
            ),
          ),
      ],
    );
  }

  Widget _variants(PharmacogenomicProfile p) => Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          Text('NON-REFERENCE POSITIONS', style: Tokens.monoLabel),
          const SizedBox(height: 5),
          for (final DetectedVariant v in p.detectedVariants.take(8))
            Text('${v.rsid ?? v.gene}  ${v.genotype}', style: Tokens.monoSm),
        ],
      );

  /// Patient view keeps genotype and variants together behind one row: for a
  /// reader who did not come looking for them, two separate rows of machine
  /// output would read as two separate things to worry about.
  Widget _foundBody(PharmacogenomicProfile p, PerDrugResult r) => Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          _facts(p, r),
          if (p.detectedVariants.isNotEmpty) ...<Widget>[
            const SizedBox(height: 8),
            _variants(p),
          ],
        ],
      );
}
