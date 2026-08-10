/// Design tokens. The single source for colour and type — no widget hardcodes a
/// colour, so a palette change is one edit rather than a search.
///
/// TWO DECISIONS HERE CARRY MEANING, not just taste.
///
/// **Unknown is `accent`, never grey.** Grey reads as "nothing happened" or
/// "disabled". An Unknown in this system is the opposite: it is the system
/// speaking, declining to assert something it cannot support. It is frequently
/// the correct and hard-won answer, and several of this project's defects were
/// cases where a confident answer appeared instead. So it gets the brand colour
/// and equal visual weight.
///
/// **Toxic and Ineffective share `danger`.** They are different mechanisms —
/// harm from exposure versus therapeutic failure — but both mean "do not proceed
/// as written", so they read the same at a glance. Severity, not hue, is what
/// separates them; see `Tokens.severityRank`.
///
/// The three-font split mirrors FIELD AUTHORSHIP, and the rule is strict:
///
///   mono  (IBM Plex Mono)  anything a machine produced — diplotypes, rsIDs,
///                          counts, phenotype codes, risk labels, CPIC text
///   serif (Newsreader)     prose written to be read by a person
///   sans  (Public Sans)    interface chrome — labels, buttons, navigation
///
/// A reader can therefore tell, without being told, which parts of the screen
/// the system measured and which parts it composed.
library;

import 'package:flutter/material.dart';

import '../models/enums.dart';

@immutable
class Tokens {
  const Tokens._();

  // --- surfaces ---------------------------------------------------------- //
  static const Color paper = Color(0xFFEDF0EA);
  static const Color card = Color(0xFFF8FAF6);

  // --- text -------------------------------------------------------------- //
  static const Color ink = Color(0xFF18211C);
  static const Color ink2 = Color(0xFF55635A);
  static const Color ink3 = Color(0xFF7D8A81);

  // --- lines ------------------------------------------------------------- //
  static const Color rule = Color(0xFFD3DACE);
  static const Color rule2 = Color(0xFFBFC8BA);

  // --- brand ------------------------------------------------------------- //
  static const Color accent = Color(0xFF5A3A5F);
  static const Color accentBg = Color(0xFFEDE4EE);
  static const Color accentRule = Color(0xFFC6ADC8);

  // --- verdicts ---------------------------------------------------------- //
  static const Color safe = Color(0xFF34633F);
  static const Color safeBg = Color(0xFFE3EDE1);
  static const Color adjust = Color(0xFF8A5A10);
  static const Color adjustBg = Color(0xFFF5EAD6);
  static const Color danger = Color(0xFF8A2E29);
  static const Color dangerBg = Color(0xFFF5E2DF);

  // --- families ---------------------------------------------------------- //
  static const String sans = 'PublicSans';
  static const String serif = 'Newsreader';
  static const String mono = 'IBMPlexMono';

  /// Ink and tint for a verdict. Unknown deliberately resolves to the brand
  /// colour — see the library doc.
  static (Color fg, Color bg) verdict(RiskLabel label) => switch (label) {
    RiskLabel.safe => (safe, safeBg),
    RiskLabel.adjustDosage => (adjust, adjustBg),
    RiskLabel.toxic => (danger, dangerBg),
    RiskLabel.ineffective => (danger, dangerBg),
    RiskLabel.unknown => (accent, accentBg),
  };

  /// Severity ordering. Toxic and Ineffective share a colour, so this is what
  /// distinguishes "stop" from "stop, urgently".
  static int severityRank(Severity s) => switch (s) {
    Severity.none => 0,
    Severity.low => 1,
    Severity.moderate => 2,
    Severity.high => 3,
    Severity.critical => 4,
  };

  // --- type styles ------------------------------------------------------- //

  /// Machine output. Anything PharmCAT or CPIC produced renders in this.
  static const TextStyle monoSm = TextStyle(
    fontFamily: mono, fontSize: 12, height: 1.45, color: ink2);
  static const TextStyle monoMd = TextStyle(
    fontFamily: mono, fontSize: 13, height: 1.45, color: ink);
  static const TextStyle monoLg = TextStyle(
    fontFamily: mono, fontSize: 15, height: 1.4,
    fontWeight: FontWeight.w500, color: ink);

  /// A small mono label above machine output, e.g. "CPIC guideline — quoted
  /// exactly". Letter-spaced so it reads as a caption, not as content.
  static const TextStyle monoLabel = TextStyle(
    fontFamily: mono, fontSize: 11, height: 1.4, letterSpacing: 0.6,
    fontWeight: FontWeight.w500, color: ink3);

  /// Prose written for a person to read.
  static const TextStyle prose = TextStyle(
    fontFamily: serif, fontSize: 16, height: 1.6, color: ink);
  static const TextStyle proseSm = TextStyle(
    fontFamily: serif, fontSize: 14.5, height: 1.6, color: ink2);

  /// The verdict word itself — large serif, because it is the one thing the
  /// reader must take away.
  static const TextStyle verdictText = TextStyle(
    fontFamily: serif, fontSize: 30, height: 1.15,
    fontWeight: FontWeight.w600, letterSpacing: -0.4);

  /// The verdict at row scale, for the summary grid. Same serif and weight as
  /// `verdictText` so a scanned row and an opened card read as the same object.
  static const TextStyle verdictRow = TextStyle(
    fontFamily: serif, fontSize: 19, height: 1.2,
    fontWeight: FontWeight.w600, letterSpacing: -0.2);

  /// Interface chrome.
  static const TextStyle uiLg = TextStyle(
    fontFamily: sans, fontSize: 19, height: 1.3,
    fontWeight: FontWeight.w600, color: ink);
  static const TextStyle uiMd = TextStyle(
    fontFamily: sans, fontSize: 14.5, height: 1.4, color: ink);
  static const TextStyle uiSm = TextStyle(
    fontFamily: sans, fontSize: 13, height: 1.4, color: ink2);
  static const TextStyle uiTiny = TextStyle(
    fontFamily: sans, fontSize: 11.5, height: 1.35,
    letterSpacing: 0.4, color: ink3);

  // --- geometry ---------------------------------------------------------- //
  /// A hairline border is the only permitted elevation. No shadows.
  static const double hairline = 1;
  static const BorderRadius radius = BorderRadius.all(Radius.circular(4));
  static const BorderRadius radiusLg = BorderRadius.all(Radius.circular(6));

  /// The narrowest layout that must remain readable.
  static const double minWidth = 360;

  static ThemeData theme() {
    final base = ThemeData.light(useMaterial3: true);
    return base.copyWith(
      scaffoldBackgroundColor: paper,
      colorScheme: base.colorScheme.copyWith(
        primary: accent,
        surface: card,
        onSurface: ink,
        error: danger,
      ),
      textTheme: base.textTheme.apply(
        fontFamily: sans, bodyColor: ink, displayColor: ink),
      dividerColor: rule,
      // Focus must be visible for keyboard users; the default is too faint on
      // a paper background.
      focusColor: accent.withValues(alpha: 0.28),
      appBarTheme: const AppBarTheme(
        backgroundColor: paper,
        surfaceTintColor: Colors.transparent,
        elevation: 0,
        foregroundColor: ink,
      ),
      cardTheme: const CardThemeData(
        color: card,
        elevation: 0,
        margin: EdgeInsets.zero,
      ),
    );
  }
}
