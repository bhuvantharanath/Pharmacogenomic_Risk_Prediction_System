/// The floor: 360px, visible focus, reduced motion, and the locked visual rules.
///
/// These are the constraints that decay silently. Nothing about a page that
/// overflows by 12px at 360px, or a control a keyboard user cannot see they
/// have landed on, shows up in a screenshot taken on a desktop — and the census
/// header in this project already overflowed at exactly this width once.
library;

import 'dart:convert';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:pharmaguard/models/analysis.dart';
import 'package:pharmaguard/screens/results_screen.dart';
import 'package:pharmaguard/theme/tokens.dart';
import 'package:pharmaguard/glossary/glossary_text.dart';
import 'package:pharmaguard/widgets/disclosure_row.dart';
import 'package:pharmaguard/widgets/view_mode.dart';

AnalyzeResponse _payload(String name) => AnalyzeResponse.fromJson(
    jsonDecode(File('../test-data/demo/outputs/$name').readAsStringSync())
        as Map<String, dynamic>);

void main() {
  setUp(resetViewMode);

  group('360px is a floor, not a target', () {
    for (final String payload in <String>[
      'S6_multidrug.json', 'S2_variants_only.json', 'S1_confident.json',
    ]) {
      for (final ViewMode mode in ViewMode.values) {
        testWidgets('$payload renders in ${mode.name} view without overflow',
            (WidgetTester t) async {
          final File f = File('../test-data/demo/outputs/$payload');
          if (!f.existsSync()) return;

          viewMode.value = mode;
          await t.binding.setSurfaceSize(const Size(Tokens.minWidth, 900));
          addTearDown(() => t.binding.setSurfaceSize(null));
          await t.pumpWidget(
              MaterialApp(home: ResultsScreen(response: _payload(payload))));
          await t.pumpAndSettle();

          expect(TestWidgetsFlutterBinding.instance.takeException(), isNull,
              reason: '$payload overflows at ${Tokens.minWidth}px in '
                  '${mode.name} view');
        });
      }
    }
  });

  group('keyboard focus is visible', () {
    testWidgets('the theme sets a focus colour strong enough to see',
        (WidgetTester t) async {
      // Flutter's default focus highlight is nearly invisible on this paper
      // background, so the theme overrides it. If that override is ever
      // dropped, keyboard users lose their place with no visible symptom.
      final ThemeData theme = Tokens.theme();
      expect(theme.focusColor, isNot(Colors.transparent));
      expect(theme.focusColor.a, greaterThan(0.2));
    });

    testWidgets('a disclosure row carries its own focus colour',
        (WidgetTester t) async {
      await t.pumpWidget(MaterialApp(
        theme: Tokens.theme(),
        home: const Scaffold(
          body: DisclosureRow(title: 'Detail', child: Text('body')),
        ),
      ));
      await t.pumpAndSettle();

      final InkWell row = t.widget<InkWell>(find.byType(InkWell).first);
      expect(row.focusColor, isNotNull);
    });

    testWidgets('a disclosure row opens from the keyboard',
        (WidgetTester t) async {
      await t.pumpWidget(MaterialApp(
        theme: Tokens.theme(),
        home: const Scaffold(
          body: DisclosureRow(title: 'Detail', child: Text('the body')),
        ),
      ));
      await t.pumpAndSettle();
      expect(find.text('the body'), findsNothing);

      await t.sendKeyEvent(LogicalKeyboardKey.tab);
      await t.pumpAndSettle();
      await t.sendKeyEvent(LogicalKeyboardKey.enter);
      await t.pumpAndSettle();

      expect(find.text('the body'), findsOneWidget);
    });
  });

  group('reduced motion is respected', () {
    test('no animated disclosure survives anywhere in the app', () {
      // `ExpansionTile` animates and offers no hook to switch that off, so the
      // app uses a row that simply appears. This is a sabotage check: the fix
      // is easy to undo by reaching for the Material widget again.
      final List<String> offenders = <String>[];
      for (final FileSystemEntity f
          in Directory('lib').listSync(recursive: true)) {
        if (f is! File || !f.path.endsWith('.dart')) continue;
        // `ExpansionTile(` — a call, not the word in the doc comment that
        // explains why it is not used.
        if (f.readAsStringSync().contains('ExpansionTile(')) {
          offenders.add(f.path);
        }
      }
      expect(offenders, isEmpty,
          reason: 'ExpansionTile animates and cannot honour reduced motion: '
              '$offenders');
    });

    testWidgets('the definition sheet appears at once when motion is off',
        (WidgetTester t) async {
      await t.pumpWidget(MediaQuery(
        data: const MediaQueryData(disableAnimations: true),
        child: MaterialApp(
          theme: Tokens.theme(),
          home: Scaffold(
            body: GlossaryScope(
              child: Builder(
                builder: (BuildContext context) => const GlossaryText(
                    'Your phenotype matters.', style: Tokens.proseSm),
              ),
            ),
          ),
        ),
      ));
      await t.pumpAndSettle();

      await t.tap(find.text('phenotype'));
      // A single frame, deliberately: with the slide transition still in place
      // the sheet is off-screen at this point and the definition unreadable.
      await t.pump();

      expect(find.text('PHENOTYPE'), findsOneWidget);
      expect(find.textContaining('What your genes actually do'), findsOneWidget);
    });

    testWidgets('and still opens normally when motion is on',
        (WidgetTester t) async {
      await t.pumpWidget(MaterialApp(
        theme: Tokens.theme(),
        home: Scaffold(
          body: GlossaryScope(
            child: const GlossaryText('Your phenotype matters.',
                style: Tokens.proseSm),
          ),
        ),
      ));
      await t.pumpAndSettle();

      await t.tap(find.text('phenotype'));
      await t.pumpAndSettle();
      expect(find.text('PHENOTYPE'), findsOneWidget);
    });
  });

  group('the locked visual rules', () {
    test('no gradients, glass, shadows, or blue chrome in the app source', () {
      final List<String> offences = <String>[];
      for (final FileSystemEntity f
          in Directory('lib').listSync(recursive: true)) {
        if (f is! File || !f.path.endsWith('.dart')) continue;
        // The printable summary carries its own print CSS, which names the
        // properties it forbids only inside test assertions, never here.
        final String src = f.readAsStringSync();
        for (final String banned in <String>[
          'LinearGradient', 'RadialGradient', 'BoxShadow', 'BackdropFilter',
          'ImageFilter.blur', 'Colors.blue',
        ]) {
          if (src.contains(banned)) offences.add('${f.path}: $banned');
        }
      }
      expect(offences, isEmpty, reason: offences.join('; '));
    });

    test('elevation stays at zero — a hairline border is the only relief', () {
      final ThemeData theme = Tokens.theme();
      expect(theme.cardTheme.elevation ?? 0, 0);
      expect(theme.appBarTheme.elevation ?? 0, 0);
      expect(Tokens.hairline, 1);
    });

    test('the three-font role split is intact', () {
      // mono = machine output, serif = prose for people, sans = chrome. If two
      // of these ever collapse to one family the reader loses the only signal
      // distinguishing what was measured from what was composed.
      expect(<String>{Tokens.mono, Tokens.serif, Tokens.sans}, hasLength(3));
      expect(Tokens.monoSm.fontFamily, Tokens.mono);
      expect(Tokens.prose.fontFamily, Tokens.serif);
      expect(Tokens.uiMd.fontFamily, Tokens.sans);
      // The verdict is serif at every size it appears in.
      expect(Tokens.verdictRow.fontFamily, Tokens.serif);
      expect(Tokens.verdictText.fontFamily, Tokens.serif);
    });
  });
}
