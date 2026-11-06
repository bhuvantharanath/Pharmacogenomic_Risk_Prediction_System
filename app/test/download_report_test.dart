/// "Download report" hands the PDF summary and the FHIR Genomics Report to
/// the download seam (audit/phase9/B9_PLAN.md, AC6).
library;

import 'dart:convert';
import 'dart:typed_data';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:pharmaguard/models/analysis.dart';
import 'package:pharmaguard/screens/results_screen.dart';

import 'support/fixtures.dart';

typedef _Download = ({String name, Uint8List bytes, String mediaType});

void main() {
  final AnalyzeResponse response = loadFixture(
    fixtureFiles().singleWhere((f) => fixtureName(f) == 'S6_multidrug'),
  );

  Future<List<_Download>> pumpAndChoose(
    WidgetTester tester,
    String item,
  ) async {
    final List<_Download> downloads = <_Download>[];
    await tester.pumpWidget(
      MaterialApp(
        home: ResultsScreen(
          response: response,
          downloader: (String name, Uint8List bytes, String mediaType) async {
            downloads.add((name: name, bytes: bytes, mediaType: mediaType));
            return 'Downloaded $name';
          },
        ),
      ),
    );
    await tester.pumpAndSettle();
    await tester.dragUntilVisible(
      find.text('Download report'),
      find.byType(Scrollable).first,
      const Offset(0, -200),
    );
    await tester.tap(find.text('Download report'));
    await tester.pumpAndSettle();
    expect(find.text('PDF summary (.pdf)'), findsOneWidget);
    expect(find.text('FHIR Genomics Report (.json)'), findsOneWidget);
    // The PDF loads the app's fonts and lays out pages: real asynchronous
    // work, so it runs outside the fake clock.
    await tester.runAsync(() async {
      await tester.tap(find.text(item));
      for (int i = 0; i < 100 && downloads.isEmpty; i++) {
        await Future<void>.delayed(const Duration(milliseconds: 50));
      }
    });
    await tester.pumpAndSettle();
    return downloads;
  }

  testWidgets('the PDF summary reaches the download seam as a PDF', (
    WidgetTester tester,
  ) async {
    final List<_Download> downloads = await pumpAndChoose(
      tester,
      'PDF summary (.pdf)',
    );
    final _Download d = downloads.single;
    expect(d.name, endsWith('.pdf'));
    expect(d.mediaType, 'application/pdf');
    expect(String.fromCharCodes(d.bytes.take(5)), '%PDF-');
    expect(find.text('Downloaded ${d.name}'), findsOneWidget);
  });

  testWidgets('the FHIR report reaches the download seam as a FHIR bundle', (
    WidgetTester tester,
  ) async {
    final List<_Download> downloads = await pumpAndChoose(
      tester,
      'FHIR Genomics Report (.json)',
    );
    final _Download d = downloads.single;
    expect(d.name, endsWith('.fhir.json'));
    expect(d.mediaType, 'application/fhir+json');
    final Map<String, dynamic> bundle =
        jsonDecode(utf8.decode(d.bytes)) as Map<String, dynamic>;
    expect(bundle['resourceType'], 'Bundle');
    expect(bundle['entry'], isNotEmpty);
  });

  testWidgets('keeps the printable summary and the JSON export', (
    WidgetTester tester,
  ) async {
    await tester.pumpWidget(
      MaterialApp(home: ResultsScreen(response: response)),
    );
    await tester.pumpAndSettle();
    await tester.dragUntilVisible(
      find.text('Download report'),
      find.byType(Scrollable).first,
      const Offset(0, -200),
    );
    expect(find.text('Printable summary'), findsOneWidget);
    expect(find.text('Export JSON'), findsOneWidget);
    expect(find.text('Copy JSON'), findsOneWidget);
  });
}
