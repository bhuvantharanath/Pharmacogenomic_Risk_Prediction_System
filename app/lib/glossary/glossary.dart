/// Plain-language definitions for the domain words this app cannot avoid.
///
/// ONE FILE, ON PURPOSE
///
/// The words here appear in explanation prose, in table labels, in warnings and
/// on the printable summary. Defined at each site they would drift, and drifting
/// definitions of "phenotype" across one screen is worse than none — a reader
/// who meets two different explanations stops trusting both.
///
/// THE RULE THAT SHAPED THE WORDING
///
/// **No definition may lean on another undefined term.** That sounds obvious and
/// is the thing that actually goes wrong: "a diplotype is your pair of star
/// alleles" is accurate, circular for the reader who needed it, and passes any
/// review that only checks correctness. Where one entry does use another, the
/// other is defined here too — `intermediate metaboliser` refers to
/// `poor metaboliser`, and that is a definition away, not a dead end.
///
/// Two words are deliberately NOT explained by their biology:
///
///   reference — the trap is not what it means but what it implies. A reader
///               hearing "matches the reference" hears "normal, fine". It means
///               "looks like the common version", which is why missing data in
///               this system produces confident wrong answers rather than
///               uncertain ones. The definition says that outright.
///
///   indeterminate — reads as failure. It is testimony: the data was read, and
///               it does not point to one answer. Silence and a stated refusal
///               are different things, and this project spent a phase on the
///               difference.
///
/// SPELLING
///
/// The app renders "metaboliser"; a reader may know it as "metabolizer". Both
/// are registered as aliases so either spelling is matched, and the definition
/// is shown under the app's own spelling rather than switching mid-screen.
library;

class GlossaryTerm {
  const GlossaryTerm({
    required this.term,
    required this.definition,
    this.aliases = const <String>[],
  });

  /// The heading shown when the definition opens.
  final String term;

  /// One or two sentences. Longer than that and it is an article, which is not
  /// what someone mid-sentence wants.
  final String definition;

  /// Other spellings and forms that should match the same entry.
  final List<String> aliases;

  List<String> get allForms => <String>[term, ...aliases];
}

const List<GlossaryTerm> kGlossary = <GlossaryTerm>[
  GlossaryTerm(
    term: 'variant',
    aliases: <String>['variants'],
    definition:
        'A spot where your DNA differs from the version most people carry. Most '
        'variants change nothing; a few change how your body handles a medicine.',
  ),
  GlossaryTerm(
    term: 'reference',
    definition:
        'The standard copy of human DNA that everything is compared against. '
        '"Matches the reference" means a spot looks like the common version — '
        'it does not mean it was checked and found healthy, which is why a spot '
        'your file never reported can be mistaken for a normal one.',
  ),
  GlossaryTerm(
    term: 'position coverage',
    aliases: <String>['positions reported', 'position'],
    definition:
        'How many of the exact DNA spots needed to read a gene actually carried '
        'a result in your file. Spots your file left out are not treated as '
        'unknown — they read as the common version, so a low count can turn '
        'into a confident wrong answer rather than a missing one.',
  ),
  GlossaryTerm(
    term: 'gene',
    aliases: <String>['genes'],
    definition:
        'A section of your DNA with a job to do. The ones here mostly build the '
        'proteins that break medicines down or move them around your body.',
  ),
  GlossaryTerm(
    term: 'star allele',
    aliases: <String>['star alleles', 'allele', 'alleles'],
    definition:
        'A named version of a gene, written with an asterisk — *1, *2, *17. '
        'Each name stands for one specific pattern of DNA differences that '
        'researchers have catalogued and studied.',
  ),
  GlossaryTerm(
    term: 'diplotype',
    aliases: <String>['diplotypes'],
    definition:
        'The two versions of a gene you carry, one inherited from each parent, '
        'written as a pair — for example *1/*2. It is what your file was read '
        'as saying, before anyone works out what it means for a medicine.',
  ),
  GlossaryTerm(
    term: 'genotype',
    aliases: <String>['genotypes'],
    definition:
        'What your DNA actually says at a particular spot. The raw reading, as '
        'opposed to any conclusion drawn from it.',
  ),
  GlossaryTerm(
    term: 'phenotype',
    aliases: <String>['phenotypes'],
    definition:
        'What your genes actually do, rather than what they are. Here it means '
        'how quickly your body deals with one particular medicine.',
  ),
  GlossaryTerm(
    term: 'poor metaboliser',
    aliases: <String>['poor metabolizer', 'poor metabolisers', 'poor metabolizers'],
    definition:
        'Your body clears this medicine far more slowly than most people do. A '
        'normal dose can build up and cause harm — or, for medicines your body '
        'has to switch on first, may never start working at all.',
  ),
  GlossaryTerm(
    term: 'intermediate metaboliser',
    aliases: <String>[
      'intermediate metabolizer', 'intermediate metabolisers',
      'intermediate metabolizers',
    ],
    definition:
        'Your body clears this medicine more slowly than most people, but not '
        'as slowly as a poor metaboliser. A standard dose may still be too much.',
  ),
  GlossaryTerm(
    term: 'normal metaboliser',
    aliases: <String>['normal metabolizer', 'extensive metaboliser'],
    definition:
        'Your body clears this medicine at the speed the standard dose was '
        'designed around.',
  ),
  GlossaryTerm(
    term: 'ultrarapid metaboliser',
    aliases: <String>[
      'ultrarapid metabolizer', 'rapid metaboliser', 'rapid metabolizer',
    ],
    definition:
        'Your body clears this medicine faster than most people. A standard '
        'dose may wear off too quickly to work — or, for medicines your body '
        'switches on, may produce a dangerously strong effect.',
  ),
  GlossaryTerm(
    term: 'indeterminate',
    definition:
        'The data was read successfully, but it does not point to a single '
        'answer, so the system declines to pick one. That is a stated result, '
        'not a missing one — it means "we looked and cannot say", which is '
        'different from "we did not look".',
  ),
  GlossaryTerm(
    term: 'VCF',
    definition:
        'The file format genomic results usually arrive in. It is a text file '
        'listing what was found at each spot that was examined.',
  ),
  GlossaryTerm(
    term: 'CPIC',
    definition:
        'The Clinical Pharmacogenetics Implementation Consortium — the group '
        'that publishes the prescribing guidance quoted in this app. Every '
        'clinical sentence here traces back to something CPIC wrote.',
  ),
];

/// Lookup by any registered spelling, case-insensitively.
final Map<String, GlossaryTerm> kGlossaryByForm = <String, GlossaryTerm>{
  for (final GlossaryTerm t in kGlossary)
    for (final String form in t.allForms) form.toLowerCase(): t,
};

/// Every matchable form, longest first.
///
/// Order matters: "poor metaboliser" must be tried before "metaboliser" would
/// be, and "star allele" before "allele", or the shorter match swallows the
/// longer one and the reader gets the wrong definition.
final List<String> kGlossaryForms = kGlossaryByForm.keys.toList()
  ..sort((String a, String b) => b.length.compareTo(a.length));
