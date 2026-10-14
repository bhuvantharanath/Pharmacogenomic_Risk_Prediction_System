import 'dart:convert';
import 'dart:io';
import '../../app/lib/models/analysis.dart';

void require(bool condition, String message) {
  if (!condition) throw StateError(message);
}

void main(List<String> args) {
  final directory = File(Platform.script.toFilePath()).parent.path;
  for (final sample in ['NA18526', 'NA12878']) {
    final raw = jsonDecode(File('$directory/$sample.analyze.json').readAsStringSync()) as Map<String, dynamic>;
    final model = AnalyzeResponse.fromJson(raw);
    final exported = model.toExportJson();
    require(model.analyses.length == 6, '$sample lost analyses');
    for (var i = 0; i < model.analyses.length; i++) {
      final parsed = model.analyses[i].toJson();
      require(jsonEncode(parsed['pharmacogenomic_profile']) == jsonEncode(raw['analyses'][i]['pharmacogenomic_profile']), '$sample profile changed');
      require(parsed['risk_assessment']['risk_label'] == raw['analyses'][i]['risk_assessment']['risk_label'], '$sample label changed');
      require(jsonEncode(parsed['llm_generated_explanation']) == jsonEncode(raw['analyses'][i]['llm_generated_explanation']), '$sample explanation changed');
    }
    final coverage = CoverageResponse.fromJson(jsonDecode(File('$directory/$sample.coverage.json').readAsStringSync()) as Map<String, dynamic>);
    require(coverage.genesTotal > 0, '$sample coverage lost');
    File('$directory/$sample.dart-export.json').writeAsStringSync(const JsonEncoder.withIndent('  ').convert(exported));
    print('$sample: six results, profiles, labels, explanation fields and coverage parsed; export generated');
  }
}
