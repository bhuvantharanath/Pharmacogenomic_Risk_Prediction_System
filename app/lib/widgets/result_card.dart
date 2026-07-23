/// The colour-coded, expandable card for a single [PerDrugResult].
library;

import 'package:flutter/material.dart';

import '../models/analysis.dart';
import '../models/enums.dart';
import '../theme/risk_style.dart';

class ResultCard extends StatelessWidget {
  const ResultCard({super.key, required this.result});

  final PerDrugResult result;

  @override
  Widget build(BuildContext context) {
    final ThemeData theme = Theme.of(context);
    final RiskStyle style = RiskStyle.of(
      context,
      result.riskAssessment.riskLabel,
    );
    final RiskAssessment risk = result.riskAssessment;
    final PharmacogenomicProfile profile = result.pharmacogenomicProfile;

    return Card(
      clipBehavior: Clip.antiAlias,
      margin: const EdgeInsets.only(bottom: 12),
      elevation: 0,
      color: style.container,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(14),
        side: BorderSide(color: style.accent.withValues(alpha: 0.45)),
      ),
      // Colour bar as a left border rather than a sibling strip: a Row with
      // CrossAxisAlignment.stretch inside a ListView has no bounded height, so
      // a strip child would be asked to lay out at infinite height and assert.
      child: DecoratedBox(
        decoration: BoxDecoration(
          border: Border(left: BorderSide(color: style.accent, width: 6)),
        ),
        child: Theme(
          // Kill the ExpansionTile's default divider lines inside a tinted card.
          data: theme.copyWith(dividerColor: Colors.transparent),
          child: ExpansionTile(
            tilePadding: const EdgeInsets.fromLTRB(14, 4, 14, 4),
            childrenPadding: const EdgeInsets.fromLTRB(14, 0, 14, 14),
            expandedCrossAxisAlignment: CrossAxisAlignment.start,
            iconColor: style.accent,
            collapsedIconColor: style.accent,
            title: _CardHeader(result: result, style: style),
            subtitle: Padding(
              padding: const EdgeInsets.only(top: 8, bottom: 4),
              child: _MetaRow(risk: risk, profile: profile, style: style),
            ),
            children: <Widget>[
              _Section(
                icon: Icons.medical_information_outlined,
                title: 'Clinical recommendation',
                accent: style.accent,
                child: _RecommendationBody(rec: result.clinicalRecommendation),
              ),
              const SizedBox(height: 14),
              _Section(
                icon: Icons.biotech_outlined,
                title: 'Pharmacogenomic detail',
                accent: style.accent,
                child: _ProfileBody(profile: profile),
              ),
              const SizedBox(height: 14),
              _Section(
                icon: Icons.auto_awesome_outlined,
                title: 'Explanation',
                accent: style.accent,
                child: _ExplanationBody(
                  explanation: result.llmGeneratedExplanation,
                  accent: style.accent,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

// --------------------------------------------------------------------------- //
// Header + collapsed summary
// --------------------------------------------------------------------------- //

class _CardHeader extends StatelessWidget {
  const _CardHeader({required this.result, required this.style});

  final PerDrugResult result;
  final RiskStyle style;

  @override
  Widget build(BuildContext context) {
    final ThemeData theme = Theme.of(context);
    final String drug = result.drug.isEmpty
        ? 'unknown'
        : result.drug[0].toUpperCase() + result.drug.substring(1);

    return Row(
      children: <Widget>[
        Expanded(
          child: Text(
            drug,
            style: theme.textTheme.titleMedium?.copyWith(
              fontWeight: FontWeight.w700,
            ),
          ),
        ),
        const SizedBox(width: 8),
        // The badge repeats the label as text so meaning never rests on colour.
        DecoratedBox(
          decoration: BoxDecoration(
            color: style.accent,
            borderRadius: BorderRadius.circular(20),
          ),
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: <Widget>[
                Icon(style.icon, size: 15, color: Colors.white),
                const SizedBox(width: 5),
                Text(
                  result.riskAssessment.riskLabel.wireValue,
                  style: theme.textTheme.labelMedium?.copyWith(
                    color: Colors.white,
                    fontWeight: FontWeight.w700,
                  ),
                ),
              ],
            ),
          ),
        ),
      ],
    );
  }
}

class _MetaRow extends StatelessWidget {
  const _MetaRow({
    required this.risk,
    required this.profile,
    required this.style,
  });

  final RiskAssessment risk;
  final PharmacogenomicProfile profile;
  final RiskStyle style;

  @override
  Widget build(BuildContext context) {
    final int pct = (risk.confidenceScore * 100).round();

    return Wrap(
      spacing: 6,
      runSpacing: 6,
      children: <Widget>[
        _Pill(
          icon: Icons.speed_outlined,
          text: severityLabel(risk.severity),
          accent: style.accent,
        ),
        _Pill(
          icon: Icons.percent_outlined,
          text: '$pct% confidence',
          accent: style.accent,
        ),
        if (profile.primaryGene != 'Unknown')
          _Pill(
            icon: Icons.science_outlined,
            text: '${profile.primaryGene} ${profile.diplotype}',
            accent: style.accent,
          ),
        _Pill(
          icon: Icons.person_search_outlined,
          text: profile.phenotype == Phenotype.unknown
              ? 'Phenotype unknown'
              : '${profile.phenotype.wireValue} · ${profile.phenotype.label}',
          accent: style.accent,
        ),
      ],
    );
  }
}

class _Pill extends StatelessWidget {
  const _Pill({required this.icon, required this.text, required this.accent});

  final IconData icon;
  final String text;
  final Color accent;

  @override
  Widget build(BuildContext context) {
    final ThemeData theme = Theme.of(context);
    return DecoratedBox(
      decoration: BoxDecoration(
        color: theme.colorScheme.surface.withValues(alpha: 0.65),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: accent.withValues(alpha: 0.35)),
      ),
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: <Widget>[
            Icon(icon, size: 13, color: theme.colorScheme.onSurfaceVariant),
            const SizedBox(width: 5),
            Text(text, style: theme.textTheme.labelSmall),
          ],
        ),
      ),
    );
  }
}

// --------------------------------------------------------------------------- //
// Expanded sections
// --------------------------------------------------------------------------- //

class _Section extends StatelessWidget {
  const _Section({
    required this.icon,
    required this.title,
    required this.accent,
    required this.child,
  });

  final IconData icon;
  final String title;
  final Color accent;
  final Widget child;

  @override
  Widget build(BuildContext context) {
    final ThemeData theme = Theme.of(context);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: <Widget>[
        Row(
          children: <Widget>[
            Icon(icon, size: 16, color: accent),
            const SizedBox(width: 6),
            Text(
              title.toUpperCase(),
              style: theme.textTheme.labelSmall?.copyWith(
                fontWeight: FontWeight.w800,
                letterSpacing: 0.7,
                color: accent,
              ),
            ),
          ],
        ),
        const SizedBox(height: 8),
        child,
      ],
    );
  }
}

/// Label-above-value pair used throughout the expanded body.
class _Field extends StatelessWidget {
  const _Field({required this.label, required this.value});

  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    final ThemeData theme = Theme.of(context);
    if (value.trim().isEmpty) return const SizedBox.shrink();

    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          Text(
            label,
            style: theme.textTheme.labelSmall?.copyWith(
              fontWeight: FontWeight.w700,
              color: theme.colorScheme.onSurfaceVariant,
            ),
          ),
          const SizedBox(height: 2),
          SelectableText(
            value,
            style: theme.textTheme.bodyMedium?.copyWith(height: 1.4),
          ),
        ],
      ),
    );
  }
}

class _RecommendationBody extends StatelessWidget {
  const _RecommendationBody({required this.rec});

  final ClinicalRecommendation rec;

  @override
  Widget build(BuildContext context) {
    final ThemeData theme = Theme.of(context);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: <Widget>[
        _Field(label: 'Action', value: rec.action),
        _Field(label: 'Dosing guidance', value: rec.dosingGuidance),
        _Field(label: 'CPIC recommendation', value: rec.cpicRecommendation),
        if (rec.alternatives.isNotEmpty)
          _Field(label: 'Alternatives', value: rec.alternatives.join(', ')),
        Wrap(
          spacing: 6,
          runSpacing: 6,
          children: <Widget>[
            Chip(
              visualDensity: VisualDensity.compact,
              label: Text('CPIC evidence: ${rec.cpicEvidenceLevel.wireValue}'),
              labelStyle: theme.textTheme.labelSmall,
            ),
            Chip(
              visualDensity: VisualDensity.compact,
              label: Text('Source: ${rec.source}'),
              labelStyle: theme.textTheme.labelSmall,
            ),
          ],
        ),
      ],
    );
  }
}

class _ProfileBody extends StatelessWidget {
  const _ProfileBody({required this.profile});

  final PharmacogenomicProfile profile;

  @override
  Widget build(BuildContext context) {
    final ThemeData theme = Theme.of(context);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: <Widget>[
        _Field(label: 'Primary gene', value: profile.primaryGene),
        _Field(label: 'Diplotype', value: profile.diplotype),
        _Field(
          label: 'Phenotype',
          value: '${profile.phenotype.wireValue} — ${profile.phenotype.label}',
        ),
        _Field(
          label: 'Activity score',
          // Null is meaningful (this gene has no activity-score model), so say
          // so rather than printing "0".
          value: profile.activityScore?.toString() ?? 'Not applicable',
        ),
        Text(
          'DETECTED VARIANTS (${profile.detectedVariants.length})',
          style: theme.textTheme.labelSmall?.copyWith(
            fontWeight: FontWeight.w700,
            color: theme.colorScheme.onSurfaceVariant,
          ),
        ),
        const SizedBox(height: 4),
        if (profile.detectedVariants.isEmpty)
          Text('None', style: theme.textTheme.bodyMedium)
        else
          ...profile.detectedVariants.map(
            (DetectedVariant v) => Padding(
              padding: const EdgeInsets.only(top: 4),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: <Widget>[
                  const Text('• '),
                  Expanded(
                    child: SelectableText(
                      '${v.displayName} · ${v.gene} · GT ${v.genotype} · ${v.function}',
                      style: theme.textTheme.bodySmall?.copyWith(height: 1.4),
                    ),
                  ),
                ],
              ),
            ),
          ),
      ],
    );
  }
}

class _ExplanationBody extends StatelessWidget {
  const _ExplanationBody({required this.explanation, required this.accent});

  final LlmGeneratedExplanation explanation;
  final Color accent;

  @override
  Widget build(BuildContext context) {
    final ThemeData theme = Theme.of(context);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: <Widget>[
        _Field(label: 'Summary', value: explanation.summary),
        _Field(label: 'Mechanism', value: explanation.mechanism),
        _Field(label: 'Variant rationale', value: explanation.variantRationale),

        // "In plain language" gets its own emphasised block: it is the part a
        // non-specialist reader will actually read.
        if (explanation.patientFriendly.trim().isNotEmpty)
          Container(
            width: double.infinity,
            margin: const EdgeInsets.only(top: 4, bottom: 10),
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: theme.colorScheme.surface.withValues(alpha: 0.7),
              borderRadius: BorderRadius.circular(10),
              // Uniform on purpose: Flutter cannot paint a non-uniform Border
              // together with a borderRadius. The accent lives in the heading
              // row below instead.
              border: Border.all(color: accent.withValues(alpha: 0.35)),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: <Widget>[
                Row(
                  children: <Widget>[
                    Icon(Icons.record_voice_over_outlined, size: 15, color: accent),
                    const SizedBox(width: 6),
                    Text(
                      'IN PLAIN LANGUAGE',
                      style: theme.textTheme.labelSmall?.copyWith(
                        fontWeight: FontWeight.w800,
                        letterSpacing: 0.7,
                        color: accent,
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 6),
                SelectableText(
                  explanation.patientFriendly,
                  style: theme.textTheme.bodyMedium?.copyWith(height: 1.45),
                ),
              ],
            ),
          ),

        // Per-result disclaimer, in addition to the app-wide banner.
        if (explanation.disclaimer.trim().isNotEmpty)
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: <Widget>[
              Icon(
                Icons.gpp_maybe_outlined,
                size: 15,
                color: theme.colorScheme.error,
              ),
              const SizedBox(width: 6),
              Expanded(
                child: Text(
                  explanation.disclaimer,
                  style: theme.textTheme.labelSmall?.copyWith(
                    color: theme.colorScheme.error,
                    fontWeight: FontWeight.w700,
                    height: 1.35,
                  ),
                ),
              ),
            ],
          ),
      ],
    );
  }
}
