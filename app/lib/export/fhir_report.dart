/// The analysis as an HL7 FHIR R4 bundle, profiled on the Genomics Reporting
/// IG 3.0.0 (STU3): the export a system can read, where the printable summary
/// is the one a person reads.
///
/// IT CLAIMS NO MORE THAN THE PRINTED PAGE
///
/// A program reading this bundle sees none of the app's context, exactly like
/// a person reading the printout. So the same rules hold, in FHIR's terms:
///
///  * The report is `partial` and every observation `preliminary`. FHIR
///    defines a `final` report as "complete and verified by an authorized
///    person". Nobody verifies these results, and those two statuses are
///    FHIR's own words for unverified data.
///  * Drug, gene, phenotype and verdict are carried as text. The only codes
///    are the ones the IG's profiles fix. Mapping them to RxNorm, HGNC or LOINC
///    answers would be new content nobody here has checked, and a phenotype
///    code depends on the gene: SLCO1B1's CPIC terms are function terms, not
///    metabolizer terms.
///  * Every analysed drug gets a Therapeutic Implication, Unknown included,
///    with the reason the screen and the printed page give. An export that
///    dropped the Unknowns would misrepresent the analysis by omission, as a
///    printout would.
///  * No Patient is made up. The VCF's sample name is a Specimen identifier:
///    it names a sample, not a person.
///
/// Pure: the same response and export time give the same bundle. Resource ids
/// are derived from the analysis, not drawn at random.
library;

import 'dart:convert';

import 'package:crypto/crypto.dart';

import '../models/analysis.dart';
import '../models/enums.dart';
import '../models/unknown_reason.dart';
import '../print/summary_document.dart' show kPrintHeaderLine;
import '../widgets/summary_grid.dart' show orderByConsequence;

const String kFhirMediaType = 'application/fhir+json';

const String _ig = 'http://hl7.org/fhir/uv/genomics-reporting';
const String _profiles = '$_ig/StructureDefinition';
const String _tbd = '$_ig/CodeSystem/tbd-codes-cs';
const String _loinc = 'http://loinc.org';

/// The printable summary's disclaimer, as plain text. A test holds it equal
/// to the HTML's, so the two cannot say different things.
const List<String> kExportDisclaimer = <String>[
  'This is not a clinical report. It was produced by a final-year student '
      'project for research and education. It has not been clinically '
      'validated, and no qualified clinical expert has reviewed the '
      'explanatory text on this page.',
  'Recommendation text on this page is quoted from published CPIC guidance '
      'via PharmCAT. Automated source checks are not human review: they cannot '
      'show that every statement here is supported, or that any of it is '
      'correct for the person this sample came from.',
  'Do not change a medicine on the strength of this page. Take it to a '
      'qualified healthcare professional.',
];

const List<Map<String, Object?>> _observationCategory = <Map<String, Object?>>[
  <String, Object?>{
    'coding': <Object?>[
      <String, Object?>{
        'system': 'http://terminology.hl7.org/CodeSystem/observation-category',
        'code': 'laboratory',
      },
    ],
  },
  <String, Object?>{
    'coding': <Object?>[
      <String, Object?>{
        'system': 'http://terminology.hl7.org/CodeSystem/v2-0074',
        'code': 'GE',
      },
    ],
  },
];

/// Pretty-printed, for the downloaded file.
String encodeFhirReport(Map<String, Object?> bundle) =>
    const JsonEncoder.withIndent('  ').convert(bundle);

/// Build the bundle. [exportedAt] is the bundle timestamp and the report's
/// `issued`; the analysis time comes from the response.
Map<String, Object?> buildFhirReport(
  AnalyzeResponse response, {
  required DateTime exportedAt,
}) {
  String id(String key) =>
      _uuid('${response.patientId}|${response.timestamp}|$key');
  String ref(String resourceId) => 'urn:uuid:$resourceId';

  final List<PerDrugResult> ordered = orderByConsequence(response.analyses);
  final String specimenId = id('specimen');
  final String documentId = id('document');
  final String? effective = _dateTime(response.timestamp);

  // One Genotype per gene assessed, shared by every drug that reads it.
  final Map<String, Map<String, Object?>> genotypes =
      <String, Map<String, Object?>>{};
  final Map<PerDrugResult, String> genotypeFor = <PerDrugResult, String>{};
  for (final PerDrugResult r in ordered) {
    final PharmacogenomicProfile p = r.pharmacogenomicProfile;
    final bool called = _known(p.primaryGene) && _known(p.diplotype);
    final String gene = called ? p.primaryGene : geneForResult(r);
    if (!_known(gene)) continue;
    final String key = called
        ? 'genotype|$gene|${p.diplotype}'
        : 'genotype|$gene|not-determined';
    final Map<String, Object?> genotype = genotypes.putIfAbsent(
      key,
      () => _genotype(
        id: id(key),
        gene: gene,
        diplotype: called ? p.diplotype : null,
        provenance: called ? p.provenanceLine : null,
        effective: effective,
        specimen: ref(specimenId),
        document: ref(documentId),
      ),
    );
    genotypeFor[r] = genotype['id']! as String;
  }

  final List<Map<String, Object?>> implications = <Map<String, Object?>>[
    for (int i = 0; i < ordered.length; i++)
      _implication(
        id: id('implication|$i|${ordered[i].drug}'),
        result: ordered[i],
        metrics: response.qualityMetrics,
        effective: effective,
        genotype: genotypeFor[ordered[i]] == null
            ? null
            : ref(genotypeFor[ordered[i]]!),
        document: ref(documentId),
      ),
  ];

  final List<Map<String, Object?>> observations = <Map<String, Object?>>[
    ...genotypes.values,
    ...implications,
  ];

  final Map<String, Object?> report = _report(
    id: id('report'),
    response: response,
    ordered: ordered,
    exportedAt: exportedAt,
    specimen: ref(specimenId),
    results: <String>[
      for (final Map<String, Object?> o in observations)
        ref(o['id']! as String),
    ],
  );

  final List<Map<String, Object?>> resources = <Map<String, Object?>>[
    report,
    _specimen(specimenId, response.patientId),
    _document(documentId),
    ...observations,
  ];

  return <String, Object?>{
    'resourceType': 'Bundle',
    'id': id('bundle'),
    'type': 'collection',
    'timestamp': _instant(exportedAt),
    'entry': <Object?>[
      for (final Map<String, Object?> resource in resources)
        <String, Object?>{
          'fullUrl': ref(resource['id']! as String),
          'resource': resource,
        },
    ],
  };
}

Map<String, Object?> _report({
  required String id,
  required AnalyzeResponse response,
  required List<PerDrugResult> ordered,
  required DateTime exportedAt,
  required String specimen,
  required List<String> results,
}) {
  final List<String> verdicts = <String>[
    for (final PerDrugResult r in ordered)
      '${r.drug}: ${r.riskAssessment.riskLabel.wireValue}',
  ];
  final String conclusion =
      '$kPrintHeaderLine. Results, most serious first: '
      '${verdicts.join('; ')}.';
  final String? provenance = provenanceText(
    response.qualityMetrics.guidelineProvenance,
  );
  final String? effective = _dateTime(response.timestamp);

  return <String, Object?>{
    'resourceType': 'DiagnosticReport',
    'id': id,
    'meta': <String, Object?>{
      'profile': <Object?>['$_profiles/genomic-report'],
    },
    'text': _narrative(<String>[
      kPrintHeaderLine,
      ...kExportDisclaimer,
      'Results, most serious first:',
      ...verdicts,
    ]),
    'extension': <Object?>[
      _codedNote('test-disclaimer', kExportDisclaimer.join(' ')),
      if (provenance != null) _codedNote('test-methodology', provenance),
    ],
    'status': 'partial',
    'category': <Object?>[
      <String, Object?>{
        'coding': <Object?>[
          <String, Object?>{
            'system': 'http://terminology.hl7.org/CodeSystem/v2-0074',
            'code': 'GE',
          },
        ],
      },
    ],
    'code': _code(_loinc, '51969-4'),
    'effectiveDateTime': ?effective,
    'issued': _instant(exportedAt),
    'specimen': <Object?>[_reference(specimen)],
    'result': <Object?>[for (final String r in results) _reference(r)],
    'conclusion': conclusion,
  };
}

/// The served guideline provenance, field by field, as the printed page lists
/// it. Null when the response carries none.
String? provenanceText(GuidelineProvenance? g) {
  if (g == null) return null;
  final List<String> rows = <String>[
    'PharmCAT ${g.pharmcatVersion}',
    if (g.cpicDataVersion.isNotEmpty) 'CPIC data version ${g.cpicDataVersion}',
    if (g.cpicGuidanceSha256.isNotEmpty)
      'CPIC table SHA-256 ${g.cpicGuidanceSha256}',
    if (g.alleleDefinitionsVersion.isNotEmpty)
      'allele definitions ${g.alleleDefinitionsVersion}',
    if (g.alleleDefinitionsSha256.isNotEmpty)
      'definitions SHA-256 ${g.alleleDefinitionsSha256}',
    if (g.pharmvarRelease.isNotEmpty) 'PharmVar release ${g.pharmvarRelease}',
    'explanations generated ${g.explanationsDate}',
    'source: ${g.cpicSource}',
  ];
  return '${rows.join('; ')}. ${g.note}'.trim();
}

Map<String, Object?> _specimen(String id, String sampleName) =>
    <String, Object?>{
      'resourceType': 'Specimen',
      'id': id,
      'text': _narrative(<String>[
        sampleName.trim().isEmpty
            ? 'The sample in the uploaded VCF. The file names no sample.'
            : 'Sample "$sampleName" in the uploaded VCF.',
      ]),
      if (sampleName.trim().isNotEmpty)
        'identifier': <Object?>[
          <String, Object?>{'value': sampleName},
        ],
      'note': <Object?>[
        <String, Object?>{
          'text':
              'The sample name in the uploaded VCF. It names a sample, not a '
              'person.',
        },
      ],
    };

Map<String, Object?> _document(String id) => <String, Object?>{
  'resourceType': 'DocumentReference',
  'id': id,
  'text': _narrative(<String>[
    'The uploaded VCF file. It is not included in this export.',
  ]),
  'status': 'current',
  'description': 'The uploaded VCF file. It is not included in this export.',
  'content': <Object?>[
    <String, Object?>{
      'attachment': <String, Object?>{'title': 'Uploaded VCF'},
    },
  ],
};

/// A gene's genotype: the served call, or, for a gene the analysis did not
/// determine, the same LOINC observation with a data-absent reason.
///
/// Only a called genotype claims the IG's Genotype profile. That profile
/// requires a value, and a not-determined genotype has none to give: filling
/// one in ("not determined" as the value) would put a non-result where a
/// result goes. So it stays a plain observation that says what is absent.
Map<String, Object?> _genotype({
  required String id,
  required String gene,
  required String? diplotype,
  required String? provenance,
  required String? effective,
  required String specimen,
  required String document,
}) => <String, Object?>{
  'resourceType': 'Observation',
  'id': id,
  if (diplotype != null)
    'meta': <String, Object?>{
      'profile': <Object?>['$_profiles/genotype'],
    },
  'text': _narrative(<String>[
    diplotype == null
        ? '$gene: genotype not determined by this analysis.'
        : '$gene $diplotype',
    ?provenance,
  ]),
  'status': 'preliminary',
  'category': _observationCategory,
  'code': _code(_loinc, '84413-4'),
  'effectiveDateTime': ?effective,
  'specimen': _reference(specimen),
  'derivedFrom': <Object?>[_reference(document)],
  // A supplied call (Phase 9 B10): named as supplied, not called.
  if (provenance != null)
    'note': <Object?>[
      <String, Object?>{'text': provenance},
    ],
  if (diplotype != null)
    'valueCodeableConcept': <String, Object?>{'text': '$gene $diplotype'}
  else
    'dataAbsentReason': <String, Object?>{
      'coding': <Object?>[
        <String, Object?>{
          'system': 'http://terminology.hl7.org/CodeSystem/data-absent-reason',
          'code': 'unknown',
        },
      ],
      'text': 'Not determined by this analysis',
    },
  'component': <Object?>[
    <String, Object?>{
      'code': _code(_loinc, '48018-6'),
      'valueCodeableConcept': <String, Object?>{'text': gene},
    },
  ],
};

Map<String, Object?> _implication({
  required String id,
  required PerDrugResult result,
  required QualityMetrics metrics,
  required String? effective,
  required String? genotype,
  required String document,
}) {
  final RiskLabel label = result.riskAssessment.riskLabel;
  final ClinicalRecommendation c = result.clinicalRecommendation;
  final bool unknown = label == RiskLabel.unknown;
  final UnknownReason? reason = unknown
      ? classifyUnknown(result, metrics)
      : null;
  final String conclusion = reason != null
      ? unknownExplanation(result, reason)
      : c.action;
  final String phenotype = unknown
      ? 'Unknown'
      : result.pharmacogenomicProfile.phenotype.wireValue;

  final List<String> notes = <String>[
    'PharmaGuard result: ${label.wireValue}',
    ?result.pharmacogenomicProfile.provenanceLine,
    if (reason == null && !c.hasMatchedCpicEntry)
      'Application limitation — not a CPIC quote.',
    if (c.hasMatchedCpicEntry &&
        c.cpicRecommendation.isNotEmpty &&
        c.cpicRecommendation != 'STUB')
      c.cpicRecommendation,
    if (reason != null) 'Why Unknown: ${reason.headline}',
    if (reason != null)
      reason.callToAction == null
          ? 'Nothing about the uploaded file would change this result.'
          : 'What would fix it: ${reason.callToAction}',
  ];

  return <String, Object?>{
    'resourceType': 'Observation',
    'id': id,
    'meta': <String, Object?>{
      'profile': <Object?>['$_profiles/therapeutic-implication'],
    },
    'text': _narrative(<String>[
      '${result.drug}: ${label.wireValue}',
      if (conclusion.trim().isNotEmpty) conclusion,
    ]),
    if (c.hasMatchedCpicEntry)
      'extension': <Object?>[
        <String, Object?>{
          'url':
              'http://hl7.org/fhir/StructureDefinition/workflow-relatedArtifact',
          'valueRelatedArtifact': <String, Object?>{
            'type': 'citation',
            'citation': c.source,
          },
        },
      ],
    'status': 'preliminary',
    'category': _observationCategory,
    'code': _code(_tbd, 'therapeutic-implication'),
    'effectiveDateTime': ?effective,
    'derivedFrom': <Object?>[
      if (genotype != null) _reference(genotype),
      _reference(document),
    ],
    'note': <Object?>[
      for (final String n in notes) <String, Object?>{'text': n},
    ],
    'component': <Object?>[
      <String, Object?>{
        'code': _code(_loinc, '51963-7'),
        'valueCodeableConcept': <String, Object?>{'text': result.drug},
      },
      <String, Object?>{
        'code': _code(_tbd, 'therapeutic-implication'),
        'valueCodeableConcept': <String, Object?>{'text': phenotype},
      },
      if (conclusion.trim().isNotEmpty)
        <String, Object?>{
          'code': _code(_tbd, 'conclusion-string'),
          'valueString': conclusion,
        },
      if (c.cpicEvidenceLevel != CpicEvidenceLevel.unknown)
        <String, Object?>{
          'code': _code(_loinc, '93044-6'),
          'valueCodeableConcept': <String, Object?>{
            'text': c.cpicEvidenceLevel.wireValue,
          },
        },
    ],
  };
}

Map<String, Object?> _codedNote(String code, String text) => <String, Object?>{
  'url': '$_profiles/genomic-report-note',
  'valueAnnotation': <String, Object?>{
    'extension': <Object?>[
      <String, Object?>{
        'url': '$_profiles/annotation-code',
        'valueCodeableConcept': _code(
          '$_ig/CodeSystem/coded-annotation-types-cs',
          code,
        ),
      },
    ],
    'text': text,
  },
};

Map<String, Object?> _code(String system, String code) => <String, Object?>{
  'coding': <Object?>[
    <String, Object?>{'system': system, 'code': code},
  ],
};

Map<String, Object?> _reference(String reference) => <String, Object?>{
  'reference': reference,
};

Map<String, Object?> _narrative(List<String> paragraphs) => <String, Object?>{
  'status': 'generated',
  'div':
      '<div xmlns="http://www.w3.org/1999/xhtml">'
      '${paragraphs.map((String p) => '<p>${_xml(p)}</p>').join()}</div>',
};

String _xml(String s) =>
    s.replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;');

bool _known(String value) =>
    value.trim().isNotEmpty && value.trim().toLowerCase() != 'unknown';

String _instant(DateTime at) => at.toUtc().toIso8601String();

/// The analysis time as a FHIR dateTime, or null when it does not parse: an
/// absent `effective` is valid FHIR, an invalid one is not.
String? _dateTime(String timestamp) {
  final DateTime? at = DateTime.tryParse(timestamp);
  return at == null ? null : _instant(at);
}

/// A version-5-shaped UUID (name-based, SHA hash) from [seed]: stable for the
/// same analysis, different across analyses.
String _uuid(String seed) {
  final List<int> h = sha256.convert(utf8.encode(seed)).bytes.sublist(0, 16);
  h[6] = (h[6] & 0x0f) | 0x50;
  h[8] = (h[8] & 0x3f) | 0x80;
  final String hex = h
      .map((int b) => b.toRadixString(16).padLeft(2, '0'))
      .join();
  return '${hex.substring(0, 8)}-${hex.substring(8, 12)}-'
      '${hex.substring(12, 16)}-${hex.substring(16, 20)}-${hex.substring(20)}';
}
