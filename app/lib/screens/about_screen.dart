/// About — what the system does, who it is for, and what it needs.
///
/// COPY PROVENANCE: the redesign brief pointed at an HTML prototype as the
/// source of truth for this text. That file was not available, so this copy was
/// written from the project's own verified documents — README, PROJECT_STATUS,
/// docs/input_requirements.md and reports/validation_report.md — rather than
/// invented. Every number here traces to a measurement in those files. If the
/// prototype's wording differs, prefer the prototype for tone but check the
/// figures against the reports before changing them.
library;

import 'package:flutter/material.dart';

import '../api/pharmaguard_api.dart';
import '../models/analysis.dart';
import '../theme/tokens.dart';

class AboutScreen extends StatefulWidget {
  const AboutScreen({super.key, this.provenance});

  /// Passed in when this screen is opened from a result, so the page states the
  /// versions that produced THAT answer rather than re-fetching the build's.
  /// Fetched from the backend when absent.
  final GuidelineProvenance? provenance;

  @override
  State<AboutScreen> createState() => _AboutScreenState();
}

class _AboutScreenState extends State<AboutScreen> {
  GuidelineProvenance? _provenance;

  @override
  void initState() {
    super.initState();
    _provenance = widget.provenance;
    if (_provenance == null) _fetch();
  }

  Future<void> _fetch() async {
    final GuidelineProvenance? p = await PharmaGuardApi().provenance();
    if (mounted && p != null) setState(() => _provenance = p);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('About', style: Tokens.uiLg)),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.fromLTRB(16, 8, 16, 40),
          child: Center(
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 760),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: <Widget>[
                  _h('What it does'),
                  _p('Some medicines work differently depending on genes you '
                      'were born with. The same dose that helps one person can '
                      'do nothing for another, or cause harm. PharmaGuard reads '
                      'a genomic file, works out the relevant genotypes, and '
                      'reports what published clinical guidance says about each '
                      'drug you ask about.'),
                  _p('It writes no clinical advice of its own. Every dosing '
                      'statement is quoted from CPIC, the body that publishes '
                      'pharmacogenomic prescribing guidelines. When the '
                      'evidence does not support an answer, it says so instead '
                      'of guessing.'),

                  _h('Who it helps'),
                  _p('Anyone prescribed one of the medicines below who already '
                      'has genomic data — and the doctor or pharmacist deciding their dose. '
                      'It is a research and teaching tool, not a clinical '
                      'service: it shows what the guidelines say, so a '
                      'conversation can start from evidence rather than from a '
                      'default dose.'),

                  _h('Medicines covered'),
                  _table(
                    <String>['Medicine', 'Used for', 'Why genetics matters'],
                    const <List<String>>[
                      ['clopidogrel', 'preventing clots after a heart procedure or stroke',
                        'a prodrug — it must be switched on by CYP2C19. Poor '
                            'metabolisers may get little or no protection'],
                      ['simvastatin', 'lowering cholesterol',
                        'reduced SLCO1B1 transport leaves more drug in the '
                            'bloodstream, raising the risk of muscle injury'],
                      ['fluorouracil', 'chemotherapy',
                        'DPYD clears the drug. Having too little of it causes '
                            'severe, sometimes fatal harm at a standard dose'],
                      ['azathioprine', 'suppressing an overactive immune system',
                        'TPMT and NUDT15 limit active metabolites. Low function '
                            'risks the bone marrow making fewer blood cells'],
                      ['warfarin', 'preventing clots',
                        'CYP2C9 affects clearance, which shifts the dose needed '
                            'to stay in range'],
                      ['codeine', 'pain relief',
                        'CYP2D6 converts it to morphine. Too little means no '
                            'relief; too much is dangerous'],
                    ],
                  ),

                  _h('Genes read'),
                  _table(
                    <String>['Gene', 'What it does'],
                    const <List<String>>[
                      ['CYP2C19', 'activates clopidogrel; clears several other drugs'],
                      ['CYP2C9', 'clears warfarin and many anti-inflammatories'],
                      ['SLCO1B1', 'transports statins into the liver'],
                      ['TPMT', 'breaks down thiopurines such as azathioprine'],
                      ['NUDT15', 'works alongside TPMT on the same drugs'],
                      ['DPYD', 'clears fluorouracil and capecitabine'],
                      ['CYP2D6', 'converts codeine to morphine — see the note below'],
                    ],
                  ),
                  const SizedBox(height: 8),
                  _note('CYP2D6 is read but never called. It is defined by '
                      'copy-number and structural changes that a VCF cannot '
                      'express, so the system reports it as not determinable '
                      'rather than guessing. Across 400 test samples it '
                      'declined every single time.'),

                  _h('What a usable file needs'),
                  _p('A GRCh38 VCF that reports every position the caller needs '
                      '— including the positions that match the reference '
                      'genome. That last part is the one that catches people out.'),
                  _p('A variants-only file, which lists just the differences, is '
                      'the common default from most pipelines. It cannot be used '
                      'here. A position that is absent is indistinguishable from '
                      'a position that was never tested, so a variant whose '
                      'key position is missing becomes invisible — and the '
                      'genotype reads as normal. Measured on synthetic files at '
                      '60% position coverage, up to 28.6% of calls came back '
                      'confidently wrong, and every wrong call reported reduced '
                      'function as normal.'),
                  _p('So the system counts what your file actually reported, '
                      'shows you the count, and declines when it is not enough.'),

                  if (_provenance != null) ...<Widget>[
                    _h('Where this guidance comes from, and when'),
                    _p('CPIC revises its guidelines. The guidance in this build '
                        'was captured on the date below and has been frozen '
                        'since, so a recommendation here reflects what CPIC '
                        'published then — not necessarily what it publishes '
                        'today. This build does not watch for changes, and says '
                        'so rather than implying it is current.'),
                    Container(
                      padding: const EdgeInsets.all(12),
                      decoration: BoxDecoration(
                        color: Tokens.paper,
                        borderRadius: Tokens.radius,
                        border: Border.all(
                            color: Tokens.rule, width: Tokens.hairline),
                      ),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: <Widget>[
                          _stamp('PharmCAT', _provenance!.pharmcatVersion),
                          if (_provenance!.cpicDataVersion.isNotEmpty)
                            _stamp('CPIC data bundle',
                                _provenance!.cpicDataVersion),
                          _stamp('Explanations generated',
                              _provenance!.explanationsDate),
                          _stamp('Source', _provenance!.cpicSource),
                        ],
                      ),
                    ),
                  ],

                  const SizedBox(height: 22),
                  Container(
                    padding: const EdgeInsets.all(13),
                    decoration: BoxDecoration(
                      color: Tokens.accentBg,
                      borderRadius: Tokens.radiusLg,
                      border: Border.all(
                          color: Tokens.accentRule, width: Tokens.hairline),
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: <Widget>[
                        Text('NOT A MEDICAL DEVICE', style: Tokens.monoLabel),
                        const SizedBox(height: 6),
                        Text(
                          'This is a final-year student project for research and '
                          'education. It has not been clinically validated and '
                          'must not be used to make decisions about anyone’s '
                          'medication. No qualified clinical expert has reviewed '
                          'the explanatory text: every clinical statement is '
                          'machine-checked to come from a published CPIC '
                          'recommendation, which verifies that nothing was '
                          'invented — not that it is correct for you. Always '
                          'consult a qualified healthcare professional.',
                          style: Tokens.proseSm.copyWith(color: Tokens.ink),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }

  /// One provenance row: a label in chrome type, a value in mono because it is
  /// a version string a machine reported, not a phrase we composed.
  Widget _stamp(String label, String value) => Padding(
        padding: const EdgeInsets.only(bottom: 5),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: <Widget>[
            SizedBox(
              width: 150,
              child: Text(label, style: Tokens.uiSm),
            ),
            Expanded(child: Text(value, style: Tokens.monoSm)),
          ],
        ),
      );

  Widget _h(String s) => Padding(
        padding: const EdgeInsets.only(top: 26, bottom: 9),
        child: Text(s, style: Tokens.uiLg),
      );

  Widget _p(String s) => Padding(
        padding: const EdgeInsets.only(bottom: 11),
        child: Text(s, style: Tokens.prose),
      );

  Widget _note(String s) => Container(
        padding: const EdgeInsets.all(11),
        decoration: BoxDecoration(
          border: Border.all(color: Tokens.rule2, width: Tokens.hairline),
          borderRadius: Tokens.radius,
        ),
        child: Text(s, style: Tokens.proseSm),
      );

  /// Stacked rows rather than a real table: at 360px a three-column table is
  /// unreadable, and horizontal scrolling for prose is worse than stacking.
  Widget _table(List<String> heads, List<List<String>> rows) => Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          for (final List<String> r in rows)
            Container(
              width: double.infinity,
              margin: const EdgeInsets.only(bottom: 8),
              padding: const EdgeInsets.all(11),
              decoration: BoxDecoration(
                color: Tokens.card,
                borderRadius: Tokens.radius,
                border: Border.all(color: Tokens.rule, width: Tokens.hairline),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: <Widget>[
                  // The identifier is machine output; the description is prose.
                  Text(r[0], style: Tokens.monoLg),
                  for (int i = 1; i < r.length; i++) ...<Widget>[
                    const SizedBox(height: 5),
                    Text(heads[i].toUpperCase(), style: Tokens.monoLabel),
                    const SizedBox(height: 2),
                    Text(r[i], style: Tokens.proseSm),
                  ],
                ],
              ),
            ),
        ],
      );
}
