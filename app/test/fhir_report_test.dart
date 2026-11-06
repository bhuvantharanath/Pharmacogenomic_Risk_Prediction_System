/// The FHIR export says what the analysis said, all of it, and claims nothing
/// more (audit/phase9/B9_PLAN.md, AC2–AC4).
///
/// Validity against the IG (AC1) is the official HL7 validator's job, in
/// `scripts/validate_fhir_exports.py`. These tests hold the content: every
/// drug present, every served string carried exactly, every Unknown carried as
/// Unknown with its reason, and statuses that say "unverified".
library;

import 'dart:convert';
import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:pharmaguard/export/fhir_report.dart';
import 'package:pharmaguard/generated/capabilities.g.dart';
import 'package:pharmaguard/models/analysis.dart';
import 'package:pharmaguard/models/unknown_reason.dart';
import 'package:pharmaguard/print/summary_document.dart';

import 'support/fixtures.dart';

const String _sd =
    'http://hl7.org/fhir/uv/genomics-reporting/StructureDefinition';
const String _tbd =
    'http://hl7.org/fhir/uv/genomics-reporting/CodeSystem/tbd-codes-cs';
const String _loinc = 'http://loinc.org';
const String _relatedArtifact =
    'http://hl7.org/fhir/StructureDefinition/workflow-relatedArtifact';

typedef Json = Map<String, dynamic>;

class _Bundle {
  _Bundle(this.json)
    : byUrl = <String, Json>{
        for (final dynamic e in json['entry'] as List<dynamic>)
          (e as Json)['fullUrl'] as String: e['resource'] as Json,
      };

  final Json json;
  final Map<String, Json> byUrl;

  Iterable<Json> ofType(String type) =>
      byUrl.values.where((Json r) => r['resourceType'] == type);

  Iterable<Json> profiled(String profile) => byUrl.values.where(
    (Json r) =>
        ((r['meta'] as Json?)?['profile'] as List<dynamic>?)?.contains(
          '$_sd/$profile',
        ) ??
        false,
  );

  Json get report => ofType('DiagnosticReport').single;

  Json implicationFor(String drug) => profiled(
    'therapeutic-implication',
  ).singleWhere((Json t) => _medication(t) == drug);
}

bool _hasCode(Json concept, String system, String code) =>
    ((concept['coding'] as List<dynamic>?) ?? <dynamic>[]).any(
      (dynamic c) => (c as Json)['system'] == system && c['code'] == code,
    );

Json? _component(Json observation, String system, String code) =>
    ((observation['component'] as List<dynamic>?) ?? <dynamic>[])
        .cast<Json>()
        .where((Json c) => _hasCode(c['code'] as Json, system, code))
        .firstOrNull;

String? _medication(Json implication) =>
    (_component(implication, _loinc, '51963-7')?['valueCodeableConcept']
            as Json?)?['text']
        as String?;

List<String> _refs(Json resource, String field) {
  final dynamic value = resource[field];
  final List<dynamic> list = value is List<dynamic> ? value : <dynamic>[?value];
  return <String>[for (final dynamic r in list) (r as Json)['reference']];
}

List<String> _notes(Json resource) => <String>[
  for (final dynamic n in (resource['note'] as List<dynamic>?) ?? <dynamic>[])
    (n as Json)['text'] as String,
];

Json? _note(Json report, String code) =>
    ((report['extension'] as List<dynamic>?) ?? <dynamic>[])
        .cast<Json>()
        .where((Json e) => e['url'] == '$_sd/genomic-report-note')
        .map((Json e) => e['valueAnnotation'] as Json)
        .where(
          (Json a) => _hasCode(
            ((a['extension'] as List<dynamic>).first
                    as Json)['valueCodeableConcept']
                as Json,
            'http://hl7.org/fhir/uv/genomics-reporting/CodeSystem/'
            'coded-annotation-types-cs',
            code,
          ),
        )
        .firstOrNull;

void main() {
  for (final File file in fixtureFiles()) {
    final String name = fixtureName(file);

    group(name, () {
      final AnalyzeResponse response = loadFixture(file);
      final Json raw = rawFixture(file);
      final List<Json> served = (raw['analyses'] as List<dynamic>).cast<Json>();
      final _Bundle bundle = _Bundle(
        jsonDecode(
              encodeFhirReport(
                buildFhirReport(response, exportedAt: kFixturePrintedAt),
              ),
            )
            as Json,
      );

      test('is the same bundle every time', () {
        String once() => encodeFhirReport(
          buildFhirReport(response, exportedAt: kFixturePrintedAt),
        );
        expect(once(), once());
        expect(bundle.json['type'], 'collection');
      });

      // ---- AC2: completeness -------------------------------------------- //

      test('has one Therapeutic Implication per analysed drug, Unknowns '
          'included', () {
        final List<String?> drugs = bundle
            .profiled('therapeutic-implication')
            .map(_medication)
            .toList();
        expect(
          drugs..sort(),
          <String>[for (final Json a in served) a['drug'] as String]..sort(),
        );
        expect(
          served.where(
            (Json a) => a['risk_assessment']['risk_label'] == 'Unknown',
          ),
          everyElement(
            predicate<Json>(
              (Json a) => drugs.contains(a['drug']),
              'is exported',
            ),
          ),
        );
      });

      test('resolves every reference inside the bundle', () {
        for (final Json r in bundle.byUrl.values) {
          for (final String field in <String>['derivedFrom', 'specimen']) {
            for (final String ref in _refs(r, field)) {
              expect(
                bundle.byUrl,
                contains(ref),
                reason: '$field of ${r['id']}',
              );
            }
          }
        }
        for (final String ref in _refs(bundle.report, 'result')) {
          expect(bundle.byUrl, contains(ref));
        }
        for (final Json t in bundle.profiled('therapeutic-implication')) {
          expect(_refs(t, 'derivedFrom'), isNotEmpty);
        }
      });

      test('lists every Observation in the report exactly once', () {
        final List<String> results = _refs(bundle.report, 'result');
        final List<String> observations = <String>[
          for (final MapEntry<String, Json> e in bundle.byUrl.entries)
            if (e.value['resourceType'] == 'Observation') e.key,
        ];
        expect(results.toSet(), hasLength(results.length));
        expect(results.toSet(), observations.toSet());
      });

      // ---- AC3: fidelity ------------------------------------------------ //

      test('carries each drug\'s served label, text and citation exactly', () {
        for (int i = 0; i < served.length; i++) {
          final Json a = served[i];
          final PerDrugResult r = response.analyses[i];
          final Json t = bundle.implicationFor(a['drug'] as String);
          final String label = a['risk_assessment']['risk_label'] as String;
          final Json rec = a['clinical_recommendation'] as Json;
          final String source = rec['source'] as String;
          final bool matched = !source.toLowerCase().contains(
            'no matching cpic entry',
          );

          expect(_notes(t).first, 'PharmaGuard result: $label');

          final String? conclusion =
              _component(t, _tbd, 'conclusion-string')?['valueString']
                  as String?;
          expect(
            conclusion,
            label == 'Unknown'
                ? unknownExplanation(
                    r,
                    classifyUnknown(r, response.qualityMetrics),
                  )
                : rec['action'],
            reason: a['drug'] as String,
          );

          final List<Json> artifacts =
              ((t['extension'] as List<dynamic>?) ?? <dynamic>[])
                  .cast<Json>()
                  .where((Json e) => e['url'] == _relatedArtifact)
                  .toList();
          if (matched) {
            expect(artifacts.single['valueRelatedArtifact'], <String, String>{
              'type': 'citation',
              'citation': source,
            });
          } else {
            expect(artifacts, isEmpty);
          }

          expect(
            (_component(
                  t,
                  _tbd,
                  'therapeutic-implication',
                )?['valueCodeableConcept']
                as Json?)?['text'],
            label == 'Unknown'
                ? 'Unknown'
                : a['pharmacogenomic_profile']['phenotype'],
          );

          if (label == 'Unknown') {
            final UnknownReason reason = classifyUnknown(
              r,
              response.qualityMetrics,
            );
            expect(_notes(t), contains('Why Unknown: ${reason.headline}'));
          }
        }
      });

      test('gives each genotype the served call, and an undetermined gene no '
          'value', () {
        for (final Json a in served) {
          final Json t = bundle.implicationFor(a['drug'] as String);
          final List<Json> genotypes = <Json>[
            for (final String ref in _refs(t, 'derivedFrom'))
              if (bundle.byUrl[ref]!['resourceType'] == 'Observation' &&
                  _hasCode(
                    bundle.byUrl[ref]!['code'] as Json,
                    _loinc,
                    '84413-4',
                  ))
                bundle.byUrl[ref]!,
          ];
          final Json p = a['pharmacogenomic_profile'] as Json;
          final String gene = p['primary_gene'] as String;
          final String diplotype = p['diplotype'] as String;

          if (gene != 'Unknown' && diplotype != 'Unknown') {
            final Json g = genotypes.single;
            expect(g['valueCodeableConcept'], <String, String>{
              'text': '$gene $diplotype',
            });
            expect(g['meta']['profile'], contains('$_sd/genotype'));
            continue;
          }
          // Served gene `Unknown`: never a value. A gene the capability table
          // names is exported as not determined; a drug outside the table has
          // no gene to name, and its implication derives from the file alone.
          final String? capabilityGene = capabilityForDrug(
            a['drug'] as String,
          )?.primaryGene;
          if (capabilityGene == null) {
            expect(genotypes, isEmpty);
            continue;
          }
          final Json g = genotypes.single;
          expect(g.containsKey('valueCodeableConcept'), isFalse);
          expect(g['dataAbsentReason'], isNotNull);
          expect(g.containsKey('meta'), isFalse, reason: 'claims no profile');
          expect(
            (_component(g, _loinc, '48018-6')!['valueCodeableConcept']
                as Json)['text'],
            capabilityGene,
          );
        }
      });

      // ---- AC4: honesty ------------------------------------------------- //

      test('says unverified: report partial, observations preliminary', () {
        expect(bundle.report['status'], 'partial');
        for (final Json o in bundle.ofType('Observation')) {
          expect(o['status'], 'preliminary');
        }
        expect(jsonEncode(bundle.json), isNot(contains('"final"')));
      });

      test('carries the printable summary\'s disclaimer', () {
        final List<String> html = htmlTextNodes(
          buildSummaryHtml(response, printedAt: kFixturePrintedAt),
        );
        final int at = html.indexOf('This is not a clinical report.');
        expect(at, isNonNegative);
        expect(
          normalizeText(kExportDisclaimer.join(' ')),
          html.sublist(at, at + 4).join(' '),
        );
        expect(
          _note(bundle.report, 'test-disclaimer')!['text'],
          kExportDisclaimer.join(' '),
        );
        final String narrative = bundle.report['text']['div'] as String;
        expect(narrative, contains(kPrintHeaderLine));
        for (final String paragraph in kExportDisclaimer) {
          expect(narrative, contains(paragraph));
        }
      });

      test('carries the served provenance', () {
        final Json g = raw['quality_metrics']['guideline_provenance'] as Json;
        final String text =
            _note(bundle.report, 'test-methodology')!['text'] as String;
        expect(
          text,
          provenanceText(response.qualityMetrics.guidelineProvenance),
        );
        for (final String field in <String>[
          'pharmcat_version',
          'cpic_data_version',
          'cpic_guidance_sha256',
          'allele_definitions_version',
          'allele_definitions_sha256',
          'pharmvar_release',
          'cpic_source',
          'note',
        ]) {
          final String value = (g[field] as String?) ?? '';
          if (value.isNotEmpty) expect(text, contains(value), reason: field);
        }
      });

      test('makes up no Patient; the sample is named only on the Specimen', () {
        expect(bundle.ofType('Patient'), isEmpty);
        final Json specimen = bundle.ofType('Specimen').single;
        expect(
          (specimen['identifier'] as List<dynamic>).single,
          <String, String>{'value': raw['patient_id'] as String},
        );
        for (final Json r in bundle.byUrl.values) {
          if (r['resourceType'] == 'Specimen') continue;
          expect(
            jsonEncode(r),
            isNot(contains(raw['patient_id'] as String)),
            reason: '${r['resourceType']} ${r['id']}',
          );
        }
      });
    });
  }
}
