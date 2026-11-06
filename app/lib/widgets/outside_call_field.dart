/// An optional CYP2D6 diplotype from a dedicated caller (Phase 9 B10).
///
/// PharmaGuard does not call CYP2D6 from a VCF, and this does not change that.
/// A caller that reads the sequencing reads can, and its diplotype is passed to
/// PharmCAT as given. Every result that rests on it is labelled "CYP2D6
/// supplied by `<caller>`, not called by PharmaGuard". The grammar below mirrors
/// the server's (backend/app/outside_calls.py) so a typo is caught before the
/// upload; the server still decides.
library;

import 'package:flutter/material.dart';

/// The callers the server accepts, in its order.
const List<String> kCyp2d6Callers = <String>[
  'Cyrius',
  'BCyrius',
  'Aldy',
  'StellarPGx',
];

const int kCyp2d6MaxLength = 80;

const String _allele = r'\*\d{1,3}(?:\.\d{3})?';
const String _copies = '$_allele(?:x(?:[2-9]|1\\d|N)|≥3)?';
const String _tandem = '$_copies(?:\\+$_copies)*';
const String _combination = '\\[$_copies(?: \\+ $_copies)+\\]';
const String _haplotype = '(?:$_combination|$_tandem)';

/// Star alleles, copy numbers (x2, xN, the binned ≥3), tandems and bracketed
/// combinations, as PharmCAT's outside-call format documents them.
final RegExp kCyp2d6Diplotype = RegExp('^$_haplotype/$_haplotype\$');

/// Why the entered call cannot be sent, or null when it can (or when nothing
/// was entered). [diplotype] is the field's trimmed text.
String? outsideCallError(String diplotype, String? caller) {
  if (diplotype.isEmpty && caller == null) return null;
  if (diplotype.isEmpty || caller == null) {
    return 'Give both the CYP2D6 diplotype and the caller that produced it, '
        'or neither.';
  }
  if (diplotype.length > kCyp2d6MaxLength ||
      !kCyp2d6Diplotype.hasMatch(diplotype)) {
    return 'Write the CYP2D6 diplotype in star-allele notation, for example '
        '*1/*4, *1x2/*4 or *1/[*6 + *8].';
  }
  return null;
}

class OutsideCallField extends StatelessWidget {
  const OutsideCallField({
    super.key,
    required this.controller,
    required this.caller,
    required this.onCallerChanged,
    required this.enabled,
  });

  final TextEditingController controller;
  final String? caller;
  final ValueChanged<String?> onCallerChanged;
  final bool enabled;

  @override
  Widget build(BuildContext context) {
    final ThemeData theme = Theme.of(context);
    final TextStyle? note = theme.textTheme.bodySmall?.copyWith(
      color: theme.colorScheme.onSurfaceVariant,
    );
    return ValueListenableBuilder<TextEditingValue>(
      valueListenable: controller,
      builder: (BuildContext context, TextEditingValue value, _) {
        final String entered = value.text.trim();
        final String? error = entered.isEmpty
            ? null
            : outsideCallError(entered, caller ?? '');
        return Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: <Widget>[
            Text(
              'Optional: CYP2D6 from a dedicated caller',
              style: theme.textTheme.titleSmall,
            ),
            const SizedBox(height: 4),
            Text(
              'PharmaGuard does not call CYP2D6 from a VCF. If Cyrius, '
              'BCyrius, Aldy or StellarPGx called it from this person’s '
              'BAM/CRAM, enter its diplotype here. It is used as given and '
              'every result from it is labelled as supplied, not called.',
              style: note,
            ),
            const SizedBox(height: 10),
            TextField(
              controller: controller,
              enabled: enabled,
              maxLength: kCyp2d6MaxLength,
              decoration: InputDecoration(
                labelText: 'CYP2D6 diplotype',
                hintText: '*1/*4',
                border: const OutlineInputBorder(),
                errorText: error == null || caller == null ? null : error,
              ),
            ),
            const SizedBox(height: 6),
            DropdownButtonFormField<String>(
              initialValue: caller,
              decoration: const InputDecoration(
                labelText: 'Called by',
                border: OutlineInputBorder(),
              ),
              items: <DropdownMenuItem<String>>[
                for (final String name in kCyp2d6Callers)
                  DropdownMenuItem<String>(value: name, child: Text(name)),
              ],
              onChanged: enabled ? onCallerChanged : null,
            ),
            if (entered.isNotEmpty &&
                caller != null &&
                error == null) ...<Widget>[
              const SizedBox(height: 6),
              Text(
                'Codeine will be answered from this call. The coverage '
                'preview above still lists it as Unknown, because the preview '
                'reads only the VCF.',
                style: note,
              ),
            ],
          ],
        );
      },
    );
  }
}
