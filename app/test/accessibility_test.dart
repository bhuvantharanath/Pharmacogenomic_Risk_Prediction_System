/// Accessibility, measured rather than asserted by eye (Phase 9 B12,
/// audit/phase9/B12_PLAN.md, AC1–AC5).
///
/// A8 measured the live client by hand and wrote the numbers into
/// `audit/phase9/a8/contrast.txt`. These tests recompute them from the tokens
/// so the figures cannot quietly rot, and they fail on a new use site that no
/// pair covers, rather than passing because nobody looked.
library;

import 'dart:io';
import 'dart:math' as math;

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:pharmaguard/models/analysis.dart';
import 'package:pharmaguard/models/enums.dart';
import 'package:pharmaguard/screens/results_screen.dart';
import 'package:pharmaguard/theme/risk_style.dart';
import 'package:pharmaguard/theme/tokens.dart';
import 'package:pharmaguard/widgets/message_text.dart';
import 'package:pharmaguard/widgets/sample_files.dart';

import 'support/fixtures.dart';

// --- WCAG 2.2 ------------------------------------------------------------ //

double _channel(int v) {
  final double c = v / 255;
  return c <= 0.04045
      ? c / 12.92
      : math.pow((c + 0.055) / 1.055, 2.4) as double;
}

double luminance(Color c) =>
    0.2126 * _channel((c.r * 255).round()) +
    0.7152 * _channel((c.g * 255).round()) +
    0.0722 * _channel((c.b * 255).round());

double contrast(Color a, Color b) {
  final double la = luminance(a), lb = luminance(b);
  return (math.max(la, lb) + 0.05) / (math.min(la, lb) + 0.05);
}

String hex(Color c) =>
    '#${((c.r * 255).round() << 16 | (c.g * 255).round() << 8 | (c.b * 255).round()).toRadixString(16).padLeft(6, '0').toUpperCase()}';

/// AA for body text.
const double kText = 4.5;

/// 1.4.11, for what identifies a control.
const double kNonText = 3.0;

void main() {
  group('AC1: contrast', () {
    test('the arithmetic reproduces what A8 published', () {
      // A8 measured the tokens B12 does not change. If this drifts, the two
      // measurements are no longer comparable and nothing below means much.
      const Map<String, (Color, Color, double)> published =
          <String, (Color, Color, double)>{
            'ink on paper': (Tokens.ink, Tokens.paper, 14.34),
            'ink2 on paper': (Tokens.ink2, Tokens.paper, 5.50),
            'ink2 on card': (Tokens.ink2, Tokens.card, 6.03),
            'accent on paper': (Tokens.accent, Tokens.paper, 8.28),
            'accent on accentBg': (Tokens.accent, Tokens.accentBg, 7.68),
            'safe on safeBg': (Tokens.safe, Tokens.safeBg, 5.82),
            'adjust on adjustBg': (Tokens.adjust, Tokens.adjustBg, 4.96),
            'adjust on card': (Tokens.adjust, Tokens.card, 5.63),
            'danger on dangerBg': (Tokens.danger, Tokens.dangerBg, 6.72),
            'rule on card': (Tokens.rule, Tokens.card, 1.36),
            'rule2 on card': (Tokens.rule2, Tokens.card, 1.64),
            'accentRule on card': (Tokens.accentRule, Tokens.card, 1.96),
          };
      published.forEach((String name, (Color, Color, double) p) {
        expect(
          contrast(p.$1, p.$2),
          closeTo(p.$3, 0.01),
          reason: '$name: A8 recorded ${p.$3}',
        );
      });
    });

    test('every colour used as text clears AA on both surfaces', () {
      // ink3's three text sites are the ones A8 failed; the others were
      // already passing and are here so a regression in either shows up.
      const Map<String, Color> textInk = <String, Color>{
        'ink': Tokens.ink,
        'ink2': Tokens.ink2,
        'ink3': Tokens.ink3,
        'accent': Tokens.accent,
      };
      for (final MapEntry<String, Color> e in textInk.entries) {
        for (final (String, Color) bg in <(String, Color)>[
          ('paper', Tokens.paper),
          ('card', Tokens.card),
        ]) {
          expect(
            contrast(e.value, bg.$2),
            greaterThanOrEqualTo(kText),
            reason: '${e.key} ${hex(e.value)} on ${bg.$1} ${hex(bg.$2)}',
          );
        }
      }
    });

    test(
      'every verdict ink clears AA on its own tint, on card and on paper',
      () {
        for (final RiskLabel label in RiskLabel.values) {
          final (Color fg, Color bg) = Tokens.verdict(label);
          for (final (String, Color) on in <(String, Color)>[
            ('its tint', bg),
            ('card', Tokens.card),
            ('paper', Tokens.paper),
          ]) {
            expect(
              contrast(fg, on.$2),
              greaterThanOrEqualTo(kText),
              reason: '${label.name} ink ${hex(fg)} on ${on.$1}',
            );
          }
        }
      },
    );

    test("a control's edge clears the non-text minimum on both surfaces", () {
      for (final MapEntry<String, Color> e in <String, Color>{
        'controlEdge': Tokens.controlEdge,
        'accentControlEdge': Tokens.accentControlEdge,
      }.entries) {
        for (final (String, Color) bg in <(String, Color)>[
          ('paper', Tokens.paper),
          ('card', Tokens.card),
        ]) {
          expect(
            contrast(e.value, bg.$2),
            greaterThanOrEqualTo(kNonText),
            reason: '${e.key} ${hex(e.value)} on ${bg.$1}',
          );
        }
      }
    });

    test(
      'an icon or swatch that carries meaning clears the non-text minimum',
      () {
        expect(
          contrast(Tokens.ink3, Tokens.paper),
          greaterThanOrEqualTo(kNonText),
        );
        expect(
          contrast(Tokens.ink3, Tokens.card),
          greaterThanOrEqualTo(kNonText),
        );
        for (final RiskLabel label in RiskLabel.values) {
          final (Color fg, _) = Tokens.verdict(label);
          expect(
            contrast(fg, Tokens.card),
            greaterThanOrEqualTo(kNonText),
            reason: '${label.name} icon on card',
          );
        }
      },
    );

    test('no control boundary still uses a decorative hairline', () {
      // The source is the subject here: a new control drawn with `rule` or
      // `rule2` must fail, which a colour-only check could never catch.
      const Map<String, List<String>> boundaries = <String, List<String>>{
        'lib/widgets/file_readiness.dart': <String>['border: Border.all('],
        'lib/widgets/view_toggle.dart': <String>[
          'border: Border.all(',
          'left: BorderSide(',
        ],
        'lib/widgets/summary_grid.dart': <String>['border: Border.all('],
        'lib/widgets/verdict_card.dart': <String>[': Border.all('],
      };
      boundaries.forEach((String path, List<String> anchors) {
        final List<String> lines = File(path).readAsLinesSync();
        for (final String anchor in anchors) {
          final int at = lines.indexWhere((String l) => l.contains(anchor));
          expect(at, isNot(-1), reason: '$path no longer contains $anchor');
          final String window = lines
              .sublist(at, math.min(at + 5, lines.length))
              .join(' ');
          expect(
            // Either controlEdge or accentControlEdge; case-folded so one
            // check covers both.
            window.toLowerCase(),
            contains('controledge'),
            reason:
                '$path near "$anchor" draws a control with a decorative '
                'hairline; use Tokens.controlEdge',
          );
        }
      });
    });
  });

  group('AC2: control names are unique', () {
    testWidgets('each sample\'s buttons name that sample', (
      WidgetTester tester,
    ) async {
      final SemanticsHandle handle = tester.ensureSemantics();
      await tester.binding.setSurfaceSize(const Size(1280, 2400));
      addTearDown(() => tester.binding.setSurfaceSize(null));
      await tester.pumpWidget(
        MaterialApp(
          theme: Tokens.theme(),
          home: Scaffold(
            body: SingleChildScrollView(
              child: SampleFilesCard(
                busy: false,
                onTry: (SampleFile _) {},
                onDownload: (SampleFile _) {},
              ),
            ),
          ),
        ),
      );
      await tester.pumpAndSettle();

      // Read each button's own node rather than walking the tree: the tree
      // walk needs APIs Flutter has deprecated, and the gate runs a plain
      // `flutter analyze`, which must stay clean.
      final List<String> buttonNames = <String>[
        for (final Element e
            in find
                .byWidgetPredicate((Widget w) => w is ButtonStyleButton)
                .evaluate())
          tester.getSemantics(find.byWidget(e.widget)).label,
      ];

      expect(buttonNames.length, greaterThanOrEqualTo(kSampleFiles.length * 2));
      expect(
        buttonNames.length,
        buttonNames.toSet().length,
        reason: 'duplicate button names: $buttonNames',
      );
      for (final SampleFile s in kSampleFiles) {
        expect(
          buttonNames.where((String n) => n.contains(s.title)).length,
          2,
          reason: '${s.title} should name both its buttons',
        );
      }
      handle.dispose();
    });
  });

  group('AC3: messages are named, not bare textboxes', () {
    test('the name carries the kind as well as the words', () {
      expect(
        MessageText.nameFor('It is busy', 'Server busy'),
        'Server busy. It is busy',
      );
      expect(MessageText.nameFor('It is busy', null), 'It is busy');
    });

    testWidgets('a message exposes a named, read-only node', (
      WidgetTester tester,
    ) async {
      final SemanticsHandle handle = tester.ensureSemantics();
      await tester.pumpWidget(
        const MaterialApp(
          home: Scaffold(
            body: MessageText('The server is busy', kind: 'Server busy'),
          ),
        ),
      );
      await tester.pumpAndSettle();
      expect(
        tester.getSemantics(find.byType(MessageText)),
        matchesSemantics(
          label: 'Server busy. The server is busy',
          isReadOnly: true,
          isLiveRegion: true,
        ),
      );
      handle.dispose();
    });

    test('every status or error message in the app uses it', () {
      // SelectableText is what A8 found announced as an unlabelled textbox.
      for (final String path in <String>[
        'lib/widgets/error_panel.dart',
        'lib/widgets/backend_status_banner.dart',
        'lib/widgets/version_notice.dart',
        'lib/screens/home_screen.dart',
      ]) {
        expect(
          File(path).readAsStringSync(),
          isNot(contains('SelectableText(')),
          reason: '$path shows a message as a bare textbox; use MessageText',
        );
      }
    });
  });

  group('AC4: risk is never colour alone', () {
    test('any two verdicts differ by word and by icon', () {
      for (final RiskLabel a in RiskLabel.values) {
        for (final RiskLabel b in RiskLabel.values) {
          if (a == b) continue;
          expect(a.displayValue, isNot(b.displayValue), reason: '$a vs $b');
          expect(
            riskIcon(a),
            isNot(riskIcon(b)),
            reason: '$a and $b share an icon',
          );
        }
      }
    });

    test('toxic and ineffective share a colour, which is why', () {
      expect(
        Tokens.verdict(RiskLabel.toxic),
        Tokens.verdict(RiskLabel.ineffective),
      );
      expect(riskIcon(RiskLabel.toxic), isNot(riskIcon(RiskLabel.ineffective)));
    });

    testWidgets('the icon is on screen beside the verdict', (
      WidgetTester tester,
    ) async {
      await tester.binding.setSurfaceSize(const Size(1280, 2400));
      addTearDown(() => tester.binding.setSurfaceSize(null));
      final AnalyzeResponse r = loadFixture(
        fixtureFiles().firstWhere((File f) => f.path.contains('S6_multidrug')),
      );
      await tester.pumpWidget(
        MaterialApp(
          theme: Tokens.theme(),
          home: ResultsScreen(response: r),
        ),
      );
      await tester.pumpAndSettle();
      for (final PerDrugResult a in r.analyses) {
        expect(
          find.byIcon(riskIcon(a.riskAssessment.riskLabel)),
          findsWidgets,
          reason: '${a.drug}: no icon for ${a.riskAssessment.riskLabel}',
        );
      }
    });
  });

  group('AC5: 200% text scale', () {
    for (final double scale in <double>[1.0, 1.5, 2.0]) {
      for (final Size size in <Size>[
        const Size(360, 800),
        const Size(1440, 900),
      ]) {
        testWidgets('no overflow at ${scale}x, ${size.width.toInt()}px', (
          WidgetTester tester,
        ) async {
          final List<String> overflows = <String>[];
          final void Function(FlutterErrorDetails)? prior =
              FlutterError.onError;
          FlutterError.onError = (FlutterErrorDetails d) {
            final String s = d.exceptionAsString();
            if (s.contains('overflowed')) {
              overflows.add(s.split('\n').first.trim());
            } else {
              prior?.call(d);
            }
          };
          addTearDown(() => FlutterError.onError = prior);
          await tester.binding.setSurfaceSize(size);
          addTearDown(() => tester.binding.setSurfaceSize(null));

          final AnalyzeResponse r = loadFixture(
            fixtureFiles().firstWhere(
              (File f) => f.path.contains('S6_multidrug'),
            ),
          );
          await tester.pumpWidget(
            MediaQuery(
              data: MediaQueryData(textScaler: TextScaler.linear(scale)),
              child: MaterialApp(
                theme: Tokens.theme(),
                home: ResultsScreen(response: r),
              ),
            ),
          );
          await tester.pumpAndSettle();

          // Opening a card changes how many InkWells exist, so the finder is
          // re-evaluated every time rather than counted once.
          for (int i = 0; i < 12; i++) {
            final Finder rows = find.byType(InkWell);
            if (rows.evaluate().length <= i) break;
            final Finder one = rows.at(i);
            await tester.ensureVisible(one);
            await tester.pumpAndSettle();
            await tester.tap(one, warnIfMissed: false);
            await tester.pumpAndSettle();
          }

          expect(
            overflows.toSet(),
            isEmpty,
            reason: 'at ${scale}x and ${size.width.toInt()}px',
          );
        });
      }
    }
  });
}
