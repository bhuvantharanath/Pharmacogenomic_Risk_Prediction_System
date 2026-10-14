/// The check-everything grid: one row per drug, ordered by consequence.
///
/// WHY A GRID AND NOT A LIST OF CARDS
///
/// Most people do not know which drug to ask about. Asked to name one, they
/// guess — and a system that only answers the question you already knew to ask
/// is useless to exactly the person who needs it most. So the discovery path is
/// "check everything", and checking everything produces six results, which is
/// more than anyone reads card by card.
///
/// A row therefore has to be scannable in about a second: the drug and the
/// bounded verdict. Everything else waits behind the row.
///
/// WHY THE ORDER IS NOT ALPHABETICAL
///
/// Alphabetical puts a no-adjustment row above "clopidogrel — Ineffective".
/// The reader meets two rows that change nothing before the one that does. The
/// grid is sorted by `RiskLabel.consequenceRank`, then by name for a stable
/// order — without inventing a clinical severity priority.
///
/// Rows open in place rather than navigating. A result you have to leave the
/// list to read is a result you compare from memory.
library;

import 'package:flutter/material.dart';

import '../models/analysis.dart';
import '../models/enums.dart';
import '../theme/tokens.dart';
import 'verdict_card.dart';
import 'view_mode.dart';

/// Consequence order: urgent first, Unknown last, deterministic throughout.
///
/// Returns a new list — sorting the caller's `analyses` in place would reorder
/// the exported JSON, which must keep the order the API sent.
List<PerDrugResult> orderByConsequence(List<PerDrugResult> analyses) {
  final List<PerDrugResult> ordered = List<PerDrugResult>.of(analyses);
  ordered.sort((PerDrugResult a, PerDrugResult b) {
    final int band = a.riskAssessment.riskLabel.consequenceRank
        .compareTo(b.riskAssessment.riskLabel.consequenceRank);
    if (band != 0) return band;

    // Alphabetical within a band, so the order never depends on the
    // sequence the drugs happened to be typed in.
    return a.drug.toLowerCase().compareTo(b.drug.toLowerCase());
  });
  return ordered;
}

class SummaryGrid extends StatefulWidget {
  const SummaryGrid({
    super.key,
    required this.analyses,
    required this.metrics,
    required this.mode,
    this.startExpanded = false,
  });

  final List<PerDrugResult> analyses;
  final QualityMetrics metrics;
  final ViewMode mode;

  /// Open every row on arrival. Set for short result sets, where collapsing is
  /// pure friction — one or two drugs is a reading task, not a scanning one.
  final bool startExpanded;

  @override
  State<SummaryGrid> createState() => _SummaryGridState();
}

class _SummaryGridState extends State<SummaryGrid>
    with AutomaticKeepAliveClientMixin<SummaryGrid> {
  /// Keyed by drug rather than index so the open set survives a re-sort.
  final Set<String> _open = <String>{};

  /// The grid is one child of the lazily built results list. Without this, a
  /// long scroll down to the exports disposed it, and every opened row came
  /// back closed. Kept alive only while something is open.
  @override
  bool get wantKeepAlive => _open.isNotEmpty;

  @override
  void initState() {
    super.initState();
    if (widget.startExpanded) {
      _open.addAll(widget.analyses.map((PerDrugResult r) => r.drug));
      updateKeepAlive();
    }
  }

  @override
  Widget build(BuildContext context) {
    super.build(context);
    final List<PerDrugResult> ordered = orderByConsequence(widget.analyses);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: <Widget>[
        for (final PerDrugResult r in ordered)
          _Row(
            result: r,
            metrics: widget.metrics,
            mode: widget.mode,
            open: _open.contains(r.drug),
            onToggle: () {
              setState(() {
                _open.contains(r.drug) ? _open.remove(r.drug) : _open.add(r.drug);
              });
              updateKeepAlive();
            },
          ),
      ],
    );
  }
}

class _Row extends StatelessWidget {
  const _Row({
    required this.result,
    required this.metrics,
    required this.mode,
    required this.open,
    required this.onToggle,
  });

  final PerDrugResult result;
  final QualityMetrics metrics;
  final ViewMode mode;
  final bool open;
  final VoidCallback onToggle;

  @override
  Widget build(BuildContext context) {
    final RiskAssessment risk = result.riskAssessment;
    final (Color fg, Color bg) = Tokens.verdict(risk.riskLabel);
    return Container(
      margin: const EdgeInsets.only(bottom: 10),
      decoration: BoxDecoration(
        color: Tokens.card,
        borderRadius: Tokens.radiusLg,
        border: Border.all(color: Tokens.rule, width: Tokens.hairline),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: <Widget>[
          Semantics(
            button: true,
            expanded: open,
            label: '${result.drug}: ${risk.riskLabel.displayValue}',
            excludeSemantics: true,
            child: InkWell(
              onTap: onToggle,
              borderRadius: Tokens.radiusLg,
              child: IntrinsicHeight(
                child: Row(
                  children: <Widget>[
                    // A colour rail, not a badge. The verdict is the finding,
                    // and a pill would read as a tag applied to the drug.
                    Container(width: 4, color: bg),
                    Expanded(
                      child: Padding(
                        padding:
                            const EdgeInsets.fromLTRB(12, 11, 8, 11),
                        child: _content(fg, risk),
                      ),
                    ),
                    Padding(
                      padding: const EdgeInsets.only(right: 11),
                      child: Icon(open ? Icons.remove : Icons.add,
                          size: 17, color: Tokens.ink3),
                    ),
                  ],
                ),
              ),
            ),
          ),
          if (open)
            Padding(
              padding: const EdgeInsets.fromLTRB(6, 0, 6, 6),
              child: VerdictCard(
                result: result,
                metrics: metrics,
                mode: mode,
                inGrid: true,
              ),
            ),
        ],
      ),
    );
  }

  /// At 360px the drug name and the verdict cannot share a line without one of
  /// them being clipped, and neither may be. They stack instead.
  Widget _content(Color fg, RiskAssessment risk) => Column(
    crossAxisAlignment: CrossAxisAlignment.start,
    children: <Widget>[
      Text(result.drug.toLowerCase(),
          style: Tokens.monoLabel, overflow: TextOverflow.ellipsis),
      const SizedBox(height: 3),
      Text(risk.riskLabel.displayValue,
          style: Tokens.verdictRow.copyWith(color: fg)),
      if (risk.severity != Severity.none) ...<Widget>[
        const SizedBox(height: 3),
        Text(
          'PGx interpretation only',
          style: Tokens.monoSm.copyWith(color: Tokens.ink2),
        ),
      ],
    ],
  );
}
