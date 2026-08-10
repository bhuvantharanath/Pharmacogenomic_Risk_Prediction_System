/// The glossary: coverage, circularity, and reachability.
///
/// The interesting test here is `no definition leans on an undefined term`.
/// "A diplotype is your pair of star alleles" is accurate, passes any review
/// that checks correctness, and is useless to the only person who would tap it.
/// Circularity is the failure mode of glossaries, and it is invisible unless
/// something checks for it mechanically.
library;

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:pharmaguard/glossary/glossary.dart';
import 'package:pharmaguard/glossary/glossary_text.dart';
import 'package:pharmaguard/theme/tokens.dart';

/// Words a reader with no biology background would not already know. Any of
/// these appearing inside a definition must itself be a defined term.
const List<String> _jargon = <String>[
  'allele', 'alleles', 'diplotype', 'diplotypes', 'genotype', 'genotypes',
  'phenotype', 'phenotypes', 'haplotype', 'haplotypes', 'polymorphism',
  'metaboliser', 'metabolizer', 'metabolisers', 'metabolizers',
  'substrate', 'prodrug', 'locus', 'loci', 'snp', 'zygous', 'zygosity',
  'wild-type', 'indeterminate', 'variant', 'variants', 'reference',
  'star allele', 'position coverage', 'vcf', 'cpic',
];

Future<void> _pump(WidgetTester t, Widget child, {double width = 360}) async {
  await t.binding.setSurfaceSize(Size(width, 1200));
  addTearDown(() => t.binding.setSurfaceSize(null));
  await t.pumpWidget(MaterialApp(
    theme: Tokens.theme(),
    home: Scaffold(
      body: GlossaryScope(
        child: SingleChildScrollView(child: child),
      ),
    ),
  ));
  await t.pumpAndSettle();
}

void main() {
  group('coverage', () {
    test('every term the brief named is defined', () {
      for (final String required in <String>[
        'poor metabolizer', 'intermediate metabolizer', 'diplotype',
        'star allele', 'phenotype', 'variant', 'reference',
        'position coverage', 'indeterminate',
      ]) {
        expect(kGlossaryByForm.containsKey(required), isTrue,
            reason: '"$required" has no definition');
      }
    });

    test('both spellings of metaboliser resolve to one entry', () {
      // The app renders "metaboliser"; a reader may know "metabolizer". Two
      // entries would eventually be two different definitions.
      expect(kGlossaryByForm['poor metaboliser'],
          same(kGlossaryByForm['poor metabolizer']));
    });

    test('definitions are one or two sentences, not an article', () {
      for (final GlossaryTerm t in kGlossary) {
        final int sentences = '.'.allMatches(t.definition).length;
        expect(sentences, lessThanOrEqualTo(3),
            reason: '"${t.term}" runs to $sentences sentences');
        expect(t.definition.length, lessThan(400), reason: t.term);
      }
    });
  });

  group('no definition leans on an undefined term', () {
    test('every jargon word inside a definition is itself defined', () {
      final List<String> offences = <String>[];

      for (final GlossaryTerm t in kGlossary) {
        // Remove every DEFINED form first, longest first — the same order the
        // real matcher uses. Otherwise "poor metaboliser", which is defined,
        // reports as the bare "metaboliser", which is not.
        String body = t.definition.toLowerCase();
        for (final String defined in kGlossaryForms) {
          body = body.replaceAll(defined, ' ');
        }
        for (final String word in _jargon) {
          if (!RegExp('\\b${RegExp.escape(word)}\\b').hasMatch(body)) continue;
          offences.add('"${t.term}" uses undefined "$word"');
        }
      }
      expect(offences, isEmpty, reason: offences.join('; '));
    });

    test('no definition is circular', () {
      // A term must not be EXPLAINED using itself. Scoped to the first
      // sentence, which is the definition proper: a later sentence using the
      // word after it has been defined is ordinary English, not circularity.
      for (final GlossaryTerm t in kGlossary) {
        final String first =
            t.definition.split('.').first.toLowerCase();
        expect(first, isNot(contains(t.term.toLowerCase())),
            reason: '"${t.term}" defines itself');
      }
    });
  });

  group('matching', () {
    testWidgets('the longest form wins', (WidgetTester t) async {
      // "star allele" must not be matched as "allele", and "poor metaboliser"
      // must not be matched as "metaboliser" — a shorter match here gives the
      // reader a definition of the wrong word.
      await _pump(t, const GlossaryText(
          'A star allele is written with an asterisk.', style: Tokens.proseSm));

      expect(find.text('star allele'), findsOneWidget);
      expect(find.text('allele'), findsNothing);
    });

    testWidgets('only whole words match', (WidgetTester t) async {
      await _pump(t, const GlossaryText(
          'This is invariant and repositioned.', style: Tokens.proseSm));

      // "variant" inside "invariant" and "position" inside "repositioned"
      // would both underline the middle of a word.
      expect(find.text('variant'), findsNothing);
      expect(find.text('position'), findsNothing);
    });

    testWidgets('a term is marked on first use only, per screen',
        (WidgetTester t) async {
      await _pump(t, const Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          GlossaryText('Your diplotype is *1/*2.', style: Tokens.proseSm),
          GlossaryText('That diplotype is common.', style: Tokens.proseSm),
        ],
      ));

      // Twice on screen, marked once: a page where every occurrence is
      // underlined stops reading as prose.
      expect(find.text('diplotype'), findsOneWidget);
      expect(find.textContaining('That diplotype is common'), findsOneWidget);
    });

    testWidgets('the claim survives a rebuild rather than moving',
        (WidgetTester t) async {
      await _pump(t, const Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          GlossaryText('Your diplotype is *1/*2.', style: Tokens.proseSm),
          GlossaryText('That diplotype is common.', style: Tokens.proseSm),
        ],
      ));
      await t.pump();
      await t.pump();

      // If the registry were rebuilt each frame the underline could hop to the
      // second sentence, or appear on both.
      expect(find.text('diplotype'), findsOneWidget);
    });

    testWidgets('text with no terms stays a plain label',
        (WidgetTester t) async {
      await _pump(t, const GlossaryText('Nothing technical here at all.',
          style: Tokens.proseSm));
      expect(find.text('Nothing technical here at all.'), findsOneWidget);
    });
  });

  group('reachability', () {
    testWidgets('tapping a term opens its definition', (WidgetTester t) async {
      await _pump(t, const GlossaryText('Your phenotype is what counts.',
          style: Tokens.proseSm));

      await t.tap(find.text('phenotype'));
      await t.pumpAndSettle();

      expect(find.text('PHENOTYPE'), findsOneWidget);
      expect(find.textContaining('What your genes actually do'), findsOneWidget);

      await t.tap(find.text('Close'));
      await t.pumpAndSettle();
      expect(find.text('PHENOTYPE'), findsNothing);
    });

    testWidgets('a term is reachable and operable from the keyboard',
        (WidgetTester t) async {
      await _pump(t, const GlossaryText('Your phenotype is what counts.',
          style: Tokens.proseSm));

      // The people most likely to need a definition include the people least
      // likely to be using a mouse. A TextSpan recognizer would fail here.
      await t.sendKeyEvent(LogicalKeyboardKey.tab);
      await t.pumpAndSettle();
      await t.sendKeyEvent(LogicalKeyboardKey.enter);
      await t.pumpAndSettle();

      expect(find.text('PHENOTYPE'), findsOneWidget);
    });

    testWidgets('a term announces itself as having a definition',
        (WidgetTester t) async {
      final SemanticsHandle handle = t.ensureSemantics();
      await _pump(t, const GlossaryText('Your phenotype is what counts.',
          style: Tokens.proseSm));

      expect(
        find.bySemanticsLabel(RegExp(r'phenotype\. Definition available\.')),
        findsOneWidget,
      );
      handle.dispose();
    });

    testWidgets('the definition sheet names itself for a screen reader',
        (WidgetTester t) async {
      final SemanticsHandle handle = t.ensureSemantics();
      await _pump(t, const GlossaryText('A variant is a difference.',
          style: Tokens.proseSm));

      await t.tap(find.text('variant'));
      await t.pumpAndSettle();
      expect(find.bySemanticsLabel('Definition of variant'), findsOneWidget);
      handle.dispose();
    });
  });

  group('presentation', () {
    testWidgets('marked terms use a dotted underline, not a colour',
        (WidgetTester t) async {
      await _pump(t, const GlossaryText('Your phenotype is what counts.',
          style: Tokens.proseSm));

      final Text marked = t.widget<Text>(find.text('phenotype'));
      expect(marked.style?.decoration, TextDecoration.underline);
      expect(marked.style?.decorationStyle, TextDecorationStyle.dotted);
      // Colour would read as a link out of the page; the word has to stay part
      // of the sentence it is in.
      expect(marked.style?.color, Tokens.proseSm.color);
    });
  });
}
