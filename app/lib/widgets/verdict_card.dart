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

import '../models/analysis.dart';
import '../models/enums.dart';
import '../models/unknown_reason.dart';
import '../theme/tokens.dart';
import 'coverage_census.dart';
import 'unknown_reason_panel.dart';

/// Genes that no VCF can resolve, with the reason shown in place of ticks.
const Map<String, String> _notCallableFromVcf = <String, String>{
  'CYP2D6': 'Defined by copy-number and structural variation, which a VCF '
      'cannot represent. A targeted assay is required.',
};

class VerdictCard extends StatefulWidget {
  const VerdictCard({super.key, required this.result, required this.metrics});

  final PerDrugResult result;
  final QualityMetrics metrics;

  @override
  State<VerdictCard> createState() => _VerdictCardState();
}

class _VerdictCardState extends State<VerdictCard> {
  bool _why = false;
  bool _found = false;

  @override
  Widget build(BuildContext context) {
    final r = widget.result;
    final p = r.pharmacogenomicProfile;
    final (Color fg, Color bg) = Tokens.verdict(r.riskAssessment.riskLabel);
    final GeneCoverage? cov = widget.metrics.positionCoverage[p.primaryGene];
    final String? na = _notCallableFromVcf[p.primaryGene.toUpperCase()];

    return Container(
      margin: const EdgeInsets.only(bottom: 14),
      decoration: BoxDecoration(
        color: Tokens.card,
        borderRadius: Tokens.radiusLg,
        border: Border.all(color: Tokens.rule, width: Tokens.hairline),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          _verdictPanel(r, fg, bg),
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
          _row('Why this result', _why, () => setState(() => _why = !_why),
              _whyBody(r)),
          _row('What was found in your file', _found,
              () => setState(() => _found = !_found), _foundBody(p, r)),
        ],
      ),
    );
  }

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

  Widget _row(String title, bool open, VoidCallback toggle, Widget body) =>
      Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: <Widget>[
          Semantics(
            button: true,
            expanded: open,
            label: title,
            child: InkWell(
              onTap: toggle,
              child: Padding(
                padding: const EdgeInsets.fromLTRB(14, 12, 14, 12),
                child: Row(
                  children: <Widget>[
                    Expanded(
                        child: Text(title,
                            style: Tokens.uiMd
                                .copyWith(fontWeight: FontWeight.w600))),
                    Icon(open ? Icons.remove : Icons.add,
                        size: 17, color: Tokens.ink3),
                  ],
                ),
              ),
            ),
          ),
          if (open)
            Padding(
              padding: const EdgeInsets.fromLTRB(14, 0, 14, 14),
              child: body,
            ),
          Container(height: Tokens.hairline, color: Tokens.rule),
        ],
      );

  Widget _whyBody(PerDrugResult r) => Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          // Serif: written to be read.
          Text(r.llmGeneratedExplanation.summary, style: Tokens.prose),
          if (r.llmGeneratedExplanation.mechanism.isNotEmpty) ...<Widget>[
            const SizedBox(height: 10),
            Text(r.llmGeneratedExplanation.mechanism, style: Tokens.proseSm),
          ],
          const SizedBox(height: 14),
          // Mono, under a mono label: CPIC's words, not ours.
          Text('CPIC GUIDELINE — QUOTED EXACTLY', style: Tokens.monoLabel),
          const SizedBox(height: 6),
          Container(
            width: double.infinity,
            padding: const EdgeInsets.all(11),
            decoration: BoxDecoration(
              border: Border.all(color: Tokens.rule2, width: Tokens.hairline),
              borderRadius: Tokens.radius,
            ),
            // `action` carries CPIC's DIRECTIVE ("Avoid clopidogrel if
            // possible..."). `cpic_recommendation` carries the surrounding
            // metadata — strength, population, implications. The directive is
            // what a reader needs first; an earlier version showed the metadata
            // under this label, which quoted CPIC accurately but answered a
            // question nobody asked.
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: <Widget>[
                Text(r.clinicalRecommendation.action, style: Tokens.monoMd),
                if (r.clinicalRecommendation.cpicRecommendation.isNotEmpty &&
                    r.clinicalRecommendation.cpicRecommendation != 'STUB') ...<Widget>[
                  const SizedBox(height: 9),
                  Container(height: Tokens.hairline, color: Tokens.rule),
                  const SizedBox(height: 9),
                  Text(r.clinicalRecommendation.cpicRecommendation,
                      style: Tokens.monoSm),
                ],
              ],
            ),
          ),
        ],
      );

  Widget _foundBody(PharmacogenomicProfile p, PerDrugResult r) {
    final rows = <(String, String)>[
      ('gene', p.primaryGene),
      ('diplotype', p.diplotype),
      ('phenotype', p.phenotype.wireValue),
      if (p.activityScore != null)
        ('activity score', p.activityScore!.toStringAsFixed(1)),
      ('variants reported', '${p.detectedVariants.length}'),
      ('evidence level', r.clinicalRecommendation.cpicEvidenceLevel.wireValue),
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
                SizedBox(width: 116, child: Text(k, style: Tokens.monoSm)),
                Expanded(child: Text(v, style: Tokens.monoMd)),
              ],
            ),
          ),
        if (p.detectedVariants.isNotEmpty) ...<Widget>[
          const SizedBox(height: 8),
          Text('NON-REFERENCE POSITIONS', style: Tokens.monoLabel),
          const SizedBox(height: 5),
          for (final DetectedVariant v in p.detectedVariants.take(8))
            Text('${v.rsid ?? v.gene}  ${v.genotype}', style: Tokens.monoSm),
        ],
      ],
    );
  }
}
