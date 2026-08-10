/// The patient / clinician switch.
///
/// A two-button segmented control rather than a dropdown or a settings screen:
/// the choice has exactly two values, both should be visible at once, and it is
/// something a user flips mid-conversation — a clinician turning the phone
/// around to show someone their own result.
library;

import 'package:flutter/material.dart';

import '../theme/tokens.dart';
import 'view_mode.dart';

class ViewToggle extends StatelessWidget {
  const ViewToggle({super.key, required this.mode, required this.onChanged});

  final ViewMode mode;
  final ValueChanged<ViewMode> onChanged;

  @override
  Widget build(BuildContext context) => Semantics(
    label: 'Reading view. Both views show the same result; they differ only in '
        'what is shown first.',
    child: Container(
      decoration: BoxDecoration(
        borderRadius: Tokens.radius,
        border: Border.all(color: Tokens.rule2, width: Tokens.hairline),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: <Widget>[
          // Flexible, not fixed: at 360px with a large system font the two
          // labels together exceed the width, and a control that clips is a
          // control whose second option is invisible.
          for (final ViewMode m in ViewMode.values) Flexible(
            child: _Option(
            mode: m,
            selected: m == mode,
              first: m == ViewMode.values.first,
              onTap: () => onChanged(m),
            ),
          ),
        ],
      ),
    ),
  );
}

class _Option extends StatelessWidget {
  const _Option({
    required this.mode,
    required this.selected,
    required this.first,
    required this.onTap,
  });

  final ViewMode mode;
  final bool selected;
  final bool first;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) => Semantics(
    button: true,
    selected: selected,
    label: '${mode.label}. ${mode.hint}.',
    excludeSemantics: true,
    child: InkWell(
      onTap: onTap,
      // Focus must be visible: this is a two-item control where the selected
      // state and the focused state are easy to confuse.
      focusColor: Tokens.accent.withValues(alpha: 0.28),
      borderRadius: Tokens.radius,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 7),
        decoration: BoxDecoration(
          color: selected ? Tokens.accentBg : null,
          borderRadius: Tokens.radius,
          border: first
              ? null
              : const Border(
                  left: BorderSide(color: Tokens.rule2, width: Tokens.hairline)),
        ),
        child: Text(
          mode.label,
          overflow: TextOverflow.ellipsis,
          style: Tokens.uiSm.copyWith(
            color: selected ? Tokens.accent : Tokens.ink2,
            fontWeight: selected ? FontWeight.w600 : FontWeight.w400,
          ),
        ),
      ),
    ),
  );
}
