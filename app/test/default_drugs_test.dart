/// The default drug list must answer what the sample cards promise.
///
/// WHY THIS EXISTS
///
/// The default was `codeine,warfarin,clopidogrel`. Two of those three cannot
/// produce a confident label by design — codeine needs a CYP2D6 diplotype
/// supplied alongside, warfarin is an explicit abstention — so one tap on a
/// sample checked exactly one answerable drug.
///
/// That was invisible until Phase 10 §5 replaced the bundled samples. The new
/// cards promise a Toxic fluorouracil on HG02684 and a Toxic simvastatin on
/// HG00525, and neither drug was in the default, so pressing "Try this" on
/// either returned three cards that did not contain the result the card had
/// just promised. It was found by clicking the deployed site, not by any test.
///
/// These assertions are about the PROMISE, not about a particular string: a
/// card that names a drug in its description must have that drug checked.
library;

import 'package:flutter_test/flutter_test.dart';
import 'package:pharmaguard/generated/capabilities.g.dart';
import 'package:pharmaguard/screens/home_screen.dart';
import 'package:pharmaguard/widgets/sample_files.dart';

void main() {
  List<String> defaults() =>
      kDefaultDrugs.split(',').map((String s) => s.trim()).toList();

  test('the default is every drug the build presents, and nothing invented', () {
    final List<String> presentable = kDrugCapabilities
        .where((DrugCapability c) => c.uiAvailable)
        .map((DrugCapability c) => c.drug)
        .toList();
    expect(defaults(), presentable,
        reason: 'the default drug list drifted from the capability registry');
    expect(defaults(), isNotEmpty);
  });

  test('every drug a sample card names by name is actually checked', () {
    // The card text is what a reviewer reads before pressing the button. If it
    // says "fluorouracil", the run must include fluorouracil.
    final List<String> missing = <String>[];
    for (final SampleFile sample in kSampleFiles) {
      final String text = '${sample.title} ${sample.detail}'.toLowerCase();
      for (final DrugCapability c in kDrugCapabilities) {
        if (text.contains(c.drug) && !defaults().contains(c.drug)) {
          missing.add('${sample.fileName} promises ${c.drug}');
        }
      }
    }
    expect(missing, isEmpty,
        reason: 'a sample card names a drug the default run does not check: '
            '$missing');
  });

  test('the default includes drugs that can actually return a label', () {
    // A default made only of abstentions would satisfy the test above while
    // showing a reviewer nothing but Unknown.
    final int answerable = defaults()
        .where((String d) => kDrugCapabilities
            .any((DrugCapability c) => c.drug == d && c.guidanceCapable))
        .length;
    expect(answerable, greaterThanOrEqualTo(4),
        reason: 'only $answerable of the default drugs can return a label');
  });
}
