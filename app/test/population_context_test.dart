/// South Asian context: shown beside a result with every caveat, never used
/// for it, and never exported (audit/phase9/B11_PLAN.md, AC2–AC4).
library;

import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:pharmaguard/export/fhir_report.dart';
import 'package:pharmaguard/generated/capabilities.g.dart';
import 'package:pharmaguard/models/analysis.dart';
import 'package:pharmaguard/models/population_context.dart';
import 'package:pharmaguard/models/unknown_reason.dart';
import 'package:pharmaguard/print/summary_document.dart';
import 'package:pharmaguard/widgets/population_context_panel.dart';
import 'package:pharmaguard/widgets/verdict_card.dart';
import 'package:pharmaguard/widgets/view_mode.dart';

import 'support/fixtures.dart';

Future<void> _pump(WidgetTester tester, Widget child) => tester.pumpWidget(
  MaterialApp(
    home: Scaffold(body: SingleChildScrollView(child: child)),
  ),
);

String _headline(PopulationContext c) => 'At least ${c.pooled.percent}%';

void main() {
  test('the table parses, for the six genes measured', () {
    expect(kSouthAsianContext.samples, 601);
    expect(kSouthAsianContext.cohorts, <String>[
      'PJL',
      'BEB',
      'STU',
      'ITU',
      'GIH',
    ]);
    expect(kSouthAsianContext.genes.keys.toSet(), <String>{
      'CYP2C19',
      'CYP2C9',
      'SLCO1B1',
      'TPMT',
      'NUDT15',
      'DPYD',
    });
    expect(southAsianContextFor('cyp2c19')!.pooled.percent, '57.1');
    expect(southAsianContextFor('CYP2D6'), isNull);
  });

  group('AC3: every caveat is on the panel', () {
    for (final String gene in kSouthAsianContext.genes.keys) {
      testWidgets(gene, (WidgetTester tester) async {
        final PopulationContext c = southAsianContextFor(gene)!;
        await _pump(tester, PopulationContextPanel(gene: gene));
        expect(
          find.textContaining(
            '${_headline(c)} (95% CI ${c.pooled.low}–${c.pooled.high}%) of 601 '
            'people in five South Asian 1000 Genomes cohorts',
          ),
          findsOneWidget,
        );
        for (final String cohort in kSouthAsianContext.cohorts) {
          expect(find.textContaining('$cohort  '), findsOneWidget);
        }
        expect(
          find.textContaining(
            'Context only: it does not change this '
            'result',
          ),
          findsOneWidget,
        );
        expect(find.textContaining('A lower bound'), findsOneWidget);
        expect(
          find.textContaining(
            c.positionsPresent == null
                ? 'was not measured'
                : 'carried ${c.positionsPresent} of the ${c.positionsRequired} '
                      'positions',
          ),
          findsOneWidget,
        );
        expect(find.textContaining('research-format'), findsOneWidget);
        expect(find.textContaining('collected outside India'), findsOneWidget);
        expect(
          find.textContaining('A frequency is not an outcome'),
          findsOneWidget,
        );
      });
    }

    testWidgets('DPYD says how many were Indeterminate', (
      WidgetTester tester,
    ) async {
      await _pump(tester, const PopulationContextPanel(gene: 'DPYD'));
      expect(
        find.textContaining('129 more were Indeterminate'),
        findsOneWidget,
      );
    });

    testWidgets('a gene with nothing measured shows no number', (
      WidgetTester tester,
    ) async {
      await _pump(tester, const PopulationContextPanel(gene: 'CYP2D6'));
      expect(
        find.text(
          'No South Asian figure was measured for CYP2D6, so none is '
          'shown.',
        ),
        findsOneWidget,
      );
      expect(find.textContaining('%'), findsNothing);
      await _pump(tester, const PopulationContextPanel(gene: 'Unknown'));
      expect(
        find.textContaining('No gene is assessed for this drug'),
        findsOneWidget,
      );
    });
  });

  group('AC4: each open card shows its own gene and no other', () {
    for (final File file in fixtureFiles()) {
      final AnalyzeResponse response = loadFixture(file);
      for (final PerDrugResult r in response.analyses) {
        testWidgets('${fixtureName(file)} ${r.drug}', (
          WidgetTester tester,
        ) async {
          await _pump(
            tester,
            VerdictCard(
              result: r,
              metrics: response.qualityMetrics,
              mode: ViewMode.patient,
            ),
          );
          final Finder row = find.text(kPopulationContextTitle);
          expect(row, findsOneWidget);
          // The label, as words: the constant alone would follow a change.
          expect(
            find.text('South Asian context — not used for this result'),
            findsOneWidget,
          );
          await tester.ensureVisible(row);
          await tester.pumpAndSettle();
          await tester.tap(row);
          await tester.pumpAndSettle();
          final String gene = geneForResult(r);
          final PopulationContext? own = southAsianContextFor(gene);
          for (final PopulationContext other
              in kSouthAsianContext.genes.values) {
            expect(
              find.textContaining(_headline(other)),
              identical(other, own) ? findsOneWidget : findsNothing,
              reason: '${other.gene} for ${r.drug}',
            );
          }
          if (own == null) {
            expect(
              find.text(
                gene.toLowerCase() == 'unknown'
                    ? 'No gene is assessed for this drug, so there is no '
                          'South Asian figure to show.'
                    : 'No South Asian figure was measured for $gene, so '
                          'none is shown.',
              ),
              findsOneWidget,
              reason: r.drug,
            );
            expect(find.textContaining('At least'), findsNothing);
          }
        });
      }
    }

    test('the fixtures include both kinds of card without a figure', () {
      final Set<String> genes = <String>{
        for (final File file in fixtureFiles())
          for (final PerDrugResult r in loadFixture(file).analyses)
            geneForResult(r),
      };
      expect(genes, containsAll(<String>['CYP2D6', 'Unknown']));
      // Every supported drug's own gene is exercised. NUDT15 has a figure but
      // is no drug's primary gene (azathioprine's is TPMT), so no card shows it.
      expect(genes, containsAll(kDrugCapabilities.map((c) => c.primaryGene)));
    });
  });

  group('AC2: never exported', () {
    for (final File file in fixtureFiles()) {
      test(fixtureName(file), () {
        final AnalyzeResponse response = loadFixture(file);
        final String html = buildSummaryHtml(
          response,
          printedAt: kFixturePrintedAt,
        );
        final String fhir = encodeFhirReport(
          buildFhirReport(response, exportedAt: kFixturePrintedAt),
        );
        for (final String exported in <String>[html, fhir]) {
          expect(exported, isNot(contains('South Asian')));
          expect(exported, isNot(contains('1000 Genomes cohorts')));
        }
      });
    }
  });
}
