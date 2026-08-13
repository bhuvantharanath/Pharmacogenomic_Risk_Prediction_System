/// Drift between the two deployed halves must be visible, and only visible.
///
/// The client and the backend deploy through different systems, and for one
/// release they drifted with nothing anywhere reporting it: Render's
/// `autoDeploy` flag says enabled while doing nothing, so a push moved the web
/// client and left the server on older code. The site looked healthy and simply
/// behaved like an older server.
///
/// Two properties are under test, and the second matters as much as the first:
///   1. a real mismatch is SHOWN, naming both SHAs;
///   2. everything else — local dev, an older backend, an unreachable one —
///      is SILENT, because a notice that cries wolf gets ignored, and this one
///      only earns attention by being rare.
library;

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:pharmaguard/widgets/version_notice.dart';

Future<void> _pump(WidgetTester tester, VersionSkew skew) async {
  await tester.pumpWidget(MaterialApp(
    home: Scaffold(body: VersionNotice(skew: skew)),
  ));
}

void main() {
  group('mismatch — the case this exists for', () {
    const VersionSkew skew = VersionSkew(
      expected: '1afb9495fd7da5f982974e7daef5f2db1d95f4ac',
      actual: 'c108c3e38666f978710533a2c0e234397ee73bfc',
    );

    test('is detected', () {
      expect(skew.isMismatch, isTrue);
    });

    testWidgets('names BOTH sides, shortened', (WidgetTester tester) async {
      await _pump(tester, skew);

      // Both, not just "a mismatch" — a notice that does not say which two
      // things disagree cannot be acted on.
      expect(find.textContaining('1afb949'), findsOneWidget);
      expect(find.textContaining('c108c3e'), findsOneWidget);
    });

    testWidgets('does not block use, and says results are still real',
        (WidgetTester tester) async {
      await _pump(tester, skew);

      // Not a dialog and not a route — it sits inline in the page.
      //
      // NOTE: asserting `find.byType(ModalBarrier)` finds nothing does NOT
      // test this. MaterialApp renders a ModalBarrier as part of its own
      // Navigator, so that assertion fails against the framework rather than
      // against the widget, which is a check that would have been red for a
      // reason having nothing to do with blocking.
      expect(find.byType(Dialog), findsNothing);
      expect(find.byType(AlertDialog), findsNothing);
      // It is a plain descendant of the page body, so everything else on the
      // page remains laid out and interactive alongside it.
      expect(find.byType(VersionNotice), findsOneWidget);
      expect(find.textContaining('still real'), findsOneWidget);
    });
  });

  group('silence — every case that is not drift', () {
    testWidgets('local development, where no SHA is compiled in',
        (WidgetTester tester) async {
      const VersionSkew skew = VersionSkew(expected: '', actual: 'abc1234');
      expect(skew.isMismatch, isFalse);
      await _pump(tester, skew);
      expect(find.byType(SelectableText), findsNothing);
    });

    testWidgets('a backend older than this feature, reporting no commit',
        (WidgetTester tester) async {
      const VersionSkew skew = VersionSkew(expected: 'abc1234', actual: null);
      expect(skew.isMismatch, isFalse,
          reason: 'unknown is not mismatch — warning here would fire on every '
              'load against any backend predating /ready build reporting');
      await _pump(tester, skew);
      expect(find.byType(SelectableText), findsNothing);
    });

    testWidgets('an unreachable backend, reporting an empty commit',
        (WidgetTester tester) async {
      const VersionSkew skew = VersionSkew(expected: 'abc1234', actual: '');
      expect(skew.isMismatch, isFalse);
      await _pump(tester, skew);
      expect(find.byType(SelectableText), findsNothing);
    });

    testWidgets('the halves agree', (WidgetTester tester) async {
      const String sha = '1afb9495fd7da5f982974e7daef5f2db1d95f4ac';
      const VersionSkew skew = VersionSkew(expected: sha, actual: sha);
      expect(skew.isMismatch, isFalse);
      await _pump(tester, skew);
      expect(find.byType(SelectableText), findsNothing);
    });
  });

  group('the widget renders nothing at all when there is no skew', () {
    testWidgets('it collapses, rather than leaving a gap',
        (WidgetTester tester) async {
      const String sha = 'deadbeefdeadbeefdeadbeefdeadbeefdeadbeef';
      await _pump(tester, const VersionSkew(expected: sha, actual: sha));

      final Size size = tester.getSize(find.byType(VersionNotice));
      expect(size.height, 0,
          reason: 'a zero-height SizedBox, not an empty padded container — '
              'otherwise every page carries a blank band for a notice that '
              'is almost never shown');
    });
  });
}
