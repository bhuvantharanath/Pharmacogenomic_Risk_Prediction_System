/// CYP2D6 from a dedicated caller, on the client (audit/phase9/B10_PLAN.md,
/// AC3 and AC4).
///
/// The server decides what it accepts; the field mirrors its grammar so a typo
/// is caught before a minute-long upload, and the lists below are the server
/// test's own. Every view of a supplied result must say it was supplied, not
/// called: the results row and card, the printed page, the PDF (through the
/// parity test) and the FHIR export.
library;

import 'dart:convert';
import 'dart:io';
import 'dart:typed_data';

import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:pharmaguard/api/pharmaguard_api.dart';
import 'package:pharmaguard/export/fhir_report.dart';
import 'package:pharmaguard/models/analysis.dart';
import 'package:pharmaguard/models/unknown_reason.dart';
import 'package:pharmaguard/print/summary_document.dart';
import 'package:pharmaguard/screens/results_screen.dart';
import 'package:pharmaguard/widgets/outside_call_field.dart';

import 'support/fixtures.dart';

const String kProvenance =
    'CYP2D6 supplied by Cyrius, not called by PharmaGuard.';

File _file(String name) =>
    fixtureFiles().singleWhere((File f) => fixtureName(f) == name);

/// The same lists as backend/tests/test_outside_calls.py.
const List<String> kAccepted = <String>[
  '*1/*4',
  '*4/*4',
  '*1x2/*1',
  '*1/*1x2',
  '*2x2/*4',
  '*1xN/*4',
  '*68+*4/*10',
  '*1/[*6 + *8]',
  '*1≥3/*4',
  '*1.001/*2',
  '*4/*10',
  '*999/*1',
];

final List<String> kRefused = <String>[
  '*1/*4\nCYP2C19\t*1/*1',
  '*1/*4\n',
  '*1/*4\t',
  ' *1/*4',
  'CYP2D6*1/*4',
  'cyp2d6*1/*4',
  '1/4',
  '*1',
  '*1/*4/*2',
  '*1 /*4',
  '*a/*4',
  '*1/*4;rm',
  '[*6+*8]/*1',
  '*1x1/*4',
  '${'*1+' * 26}*1/*4',
];

bool _accepted(String s) =>
    s.length <= kCyp2d6MaxLength && kCyp2d6Diplotype.hasMatch(s);

class _Capture implements HttpClientAdapter {
  _Capture(this.body);

  final String body;
  FormData? sent;

  @override
  void close({bool force = false}) {}

  @override
  Future<ResponseBody> fetch(
    RequestOptions options,
    Stream<Uint8List>? requestStream,
    Future<void>? cancelFuture,
  ) async {
    sent = options.data as FormData;
    return ResponseBody.fromString(
      body,
      200,
      headers: <String, List<String>>{
        Headers.contentTypeHeader: <String>['application/json'],
      },
    );
  }
}

void main() {
  group('the field mirrors the server grammar', () {
    for (final String s in kAccepted) {
      test('accepts ${jsonEncode(s)}', () => expect(_accepted(s), isTrue));
    }
    for (final String s in kRefused) {
      test('refuses ${jsonEncode(s)}', () => expect(_accepted(s), isFalse));
    }

    test('both or neither, then the notation', () {
      expect(outsideCallError('', null), isNull);
      expect(outsideCallError('*1/*4', null), contains('or neither'));
      expect(outsideCallError('', 'Cyrius'), contains('or neither'));
      expect(outsideCallError('*1/*4;rm', 'Cyrius'), contains('star-allele'));
      expect(outsideCallError('*1/*4', 'Cyrius'), isNull);
      // Pinned deliberately, and in the server's order: this list is a copy of
      // `app.outside_calls.CALLERS`, so a name added on one side and not the
      // other would offer the user a caller the server refuses, or hide one it
      // accepts. DRAGEN joined in Phase 10 §4.
      expect(kCyp2d6Callers, <String>[
        'Cyrius',
        'BCyrius',
        'Aldy',
        'StellarPGx',
        'DRAGEN',
      ]);
    });

    testWidgets('says what a supplied call is, and what it changes', (
      WidgetTester tester,
    ) async {
      final TextEditingController controller = TextEditingController();
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: SingleChildScrollView(
              child: OutsideCallField(
                controller: controller,
                caller: 'Cyrius',
                onCallerChanged: (_) {},
                enabled: true,
              ),
            ),
          ),
        ),
      );
      expect(
        find.textContaining('does not call CYP2D6 from a VCF'),
        findsOneWidget,
      );
      await tester.enterText(find.byType(TextField), '*1/*4');
      await tester.pump();
      expect(
        find.textContaining('Codeine will be answered from this call'),
        findsOneWidget,
      );
      await tester.enterText(find.byType(TextField), '*1/*4;rm');
      await tester.pump();
      expect(find.textContaining('star-allele notation'), findsOneWidget);
      expect(find.textContaining('Codeine will be answered'), findsNothing);
    });
  });

  group('the request', () {
    Future<FormData> send({String? diplotype, String? caller}) async {
      final _Capture capture = _Capture(
        _file('X2_supplied_cyp2d6').readAsStringSync(),
      );
      final Dio dio = Dio(BaseOptions(baseUrl: 'http://test.invalid'))
        ..httpClientAdapter = capture;
      await PharmaGuardApi(dio: dio, baseUrl: 'http://test.invalid').analyze(
        fileBytes: Uint8List.fromList(<int>[1, 2, 3]),
        fileName: 'demo.vcf',
        drugs: 'codeine',
        cyp2d6Diplotype: diplotype,
        cyp2d6Caller: caller,
      );
      return capture.sent!;
    }

    test('carries the supplied call', () async {
      final FormData form = await send(diplotype: '*4/*4', caller: 'Cyrius');
      expect(
        form.fields.map((MapEntry<String, String> e) => '${e.key}=${e.value}'),
        containsAll(<String>[
          'cyp2d6_diplotype=*4/*4',
          'cyp2d6_caller=Cyrius',
          'drugs=codeine',
        ]),
      );
    });

    test('sends nothing extra without one', () async {
      final FormData form = await send();
      expect(
        form.fields.map((MapEntry<String, String> e) => e.key),
        isNot(anyOf(contains('cyp2d6_diplotype'), contains('cyp2d6_caller'))),
      );
    });
  });

  group('every view names a supplied call', () {
    final AnalyzeResponse x2 = loadFixture(_file('X2_supplied_cyp2d6'));
    PerDrugResult drug(AnalyzeResponse r, String name) =>
        r.analyses.singleWhere((PerDrugResult a) => a.drug == name);

    test('the model', () {
      expect(drug(x2, 'codeine').pharmacogenomicProfile.suppliedBy, 'Cyrius');
      expect(
        drug(x2, 'codeine').pharmacogenomicProfile.provenanceLine,
        kProvenance,
      );
      expect(drug(x2, 'clopidogrel').pharmacogenomicProfile.suppliedBy, isNull);
      expect(
        drug(x2, 'clopidogrel').pharmacogenomicProfile.provenanceLine,
        isNull,
      );
    });

    testWidgets('the results screen', (WidgetTester tester) async {
      await tester.pumpWidget(MaterialApp(home: ResultsScreen(response: x2)));
      await tester.pumpAndSettle();
      // Once, in codeine's row header: it stays on top whether or not the
      // card under it is open (inside the grid the card has no verdict panel
      // of its own). Clopidogrel's row says nothing of the kind.
      expect(find.text(kProvenance), findsOneWidget);
    });

    test('the printed page, once per supplied result', () {
      final String html = buildSummaryHtml(x2, printedAt: kFixturePrintedAt);
      expect(RegExp(RegExp.escape(kProvenance)).allMatches(html), hasLength(1));
    });

    test('the FHIR export: the genotype and the implication', () {
      final Map<String, dynamic> bundle =
          jsonDecode(
                encodeFhirReport(
                  buildFhirReport(x2, exportedAt: kFixturePrintedAt),
                ),
              )
              as Map<String, dynamic>;
      final List<Map<String, dynamic>> observations = <Map<String, dynamic>>[
        for (final dynamic e in bundle['entry'] as List<dynamic>)
          if ((e as Map<String, dynamic>)['resource']['resourceType'] ==
              'Observation')
            e['resource'] as Map<String, dynamic>,
      ];
      List<String> notes(Map<String, dynamic> o) => <String>[
        for (final dynamic n in (o['note'] as List<dynamic>?) ?? <dynamic>[])
          (n as Map<String, dynamic>)['text'] as String,
      ];
      final Map<String, dynamic> genotype = observations.singleWhere(
        (Map<String, dynamic> o) =>
            (o['valueCodeableConcept'] as Map<String, dynamic>?)?['text'] ==
            'CYP2D6 *4/*4',
      );
      expect(notes(genotype), <String>[kProvenance]);
      final Map<String, dynamic> codeine = observations.singleWhere(
        (Map<String, dynamic> o) => jsonEncode(o).contains('"codeine"'),
      );
      expect(notes(codeine), contains(kProvenance));
    });
  });

  group('a supplied call with no CPIC phenotype', () {
    final AnalyzeResponse x3 = loadFixture(_file('X3_supplied_xn'));
    final PerDrugResult codeine = x3.analyses.single;

    test('is its own reason, and the user can fix it', () {
      final UnknownReason reason = classifyUnknown(codeine, x3.qualityMetrics);
      expect(reason, UnknownReason.suppliedNotInterpretable);
      expect(reason.isActionable, isTrue);
      expect(reason.callToAction, contains('xN'));
    });

    test('the printed page says the supplied call can be corrected, '
        'and only when there is one', () {
      const String sentence =
          'A CYP2D6 call supplied with the file is an input too, and can be '
          'corrected.';
      expect(
        buildSummaryHtml(x3, printedAt: kFixturePrintedAt),
        contains(sentence),
      );
      final AnalyzeResponse s3 = loadFixture(_file('S3_cyp2d6'));
      expect(
        buildSummaryHtml(s3, printedAt: kFixturePrintedAt),
        isNot(contains(sentence)),
      );
    });
  });
}
