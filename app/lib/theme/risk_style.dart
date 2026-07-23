/// Maps a [RiskLabel] to the colours and iconography used across the UI.
///
/// Centralised so the legend, the cards and any future chart cannot drift apart.
/// Colour alone never carries the meaning — every use site also shows the label
/// text and an icon, so the cards stay readable for colour-blind users.
library;

import 'package:flutter/material.dart';

import '../models/enums.dart';

@immutable
class RiskStyle {
  const RiskStyle({
    required this.accent,
    required this.container,
    required this.onContainer,
    required this.icon,
  });

  /// Strong colour: left edge of the card, badge fill.
  final Color accent;

  /// Tinted card background.
  final Color container;

  /// Text/icon colour that is legible on [container].
  final Color onContainer;

  final IconData icon;

  /// Resolve the palette for [label] against the ambient theme brightness.
  static RiskStyle of(BuildContext context, RiskLabel label) {
    final bool dark = Theme.of(context).brightness == Brightness.dark;

    // Two hand-picked tones per label rather than one tone plus opacity: a
    // single mid-tone that passes contrast on white fails on a dark surface.
    final (Color accent, IconData icon) = switch (label) {
      RiskLabel.safe => (
        dark ? const Color(0xFF4CC66B) : const Color(0xFF1B7F3B),
        Icons.check_circle_outline,
      ),
      RiskLabel.adjustDosage => (
        dark ? const Color(0xFFE8B33C) : const Color(0xFF9A6B00),
        Icons.tune,
      ),
      RiskLabel.toxic => (
        dark ? const Color(0xFFF16A6A) : const Color(0xFFB3261E),
        Icons.warning_amber_rounded,
      ),
      RiskLabel.ineffective => (
        dark ? const Color(0xFFF16A6A) : const Color(0xFFB3261E),
        Icons.block,
      ),
      RiskLabel.unknown => (
        dark ? const Color(0xFF9BA1A6) : const Color(0xFF5F6368),
        Icons.help_outline,
      ),
    };

    return RiskStyle(
      accent: accent,
      container: accent.withValues(alpha: dark ? 0.16 : 0.09),
      onContainer: dark ? accent : Color.alphaBlend(
        accent.withValues(alpha: 0.85),
        Colors.black,
      ),
      icon: icon,
    );
  }
}

/// Human-readable gloss for a severity level.
String severityLabel(Severity s) => switch (s) {
  Severity.none => 'No severity',
  Severity.low => 'Low severity',
  Severity.moderate => 'Moderate severity',
  Severity.high => 'High severity',
  Severity.critical => 'Critical severity',
};
