/// Text that marks domain terms on first use and explains them on demand.
///
/// FIRST USE ONLY, AND WHY
///
/// A screen where every occurrence of "phenotype" is underlined stops reading
/// as prose and starts reading as a warning. Marking the first one teaches the
/// word; marking all six decorates the page and makes the genuinely important
/// underlines — the ones on words the reader has not met — indistinguishable
/// from noise.
///
/// "First" is tracked by a [GlossaryScope] placed once per screen, and a claim
/// is held by the widget that made it, so a rebuild does not hand the underline
/// to a different sentence halfway down the page.
///
/// KEYBOARD AND SCREEN READER
///
/// Terms are `WidgetSpan`s holding a real focusable control, not `TextSpan`s
/// with a tap recognizer. A recognizer is reachable by pointer only — it does
/// not take focus, does not respond to Enter, and announces nothing. Since the
/// people most likely to need a definition include the people least likely to
/// be using a mouse, that trade is not available here.
library;

import 'package:flutter/material.dart';
import 'package:flutter/scheduler.dart';

import '../theme/tokens.dart';
import 'glossary.dart';

/// Per-screen registry of which terms have already been marked.
class GlossaryScope extends InheritedWidget {
  GlossaryScope({super.key, required super.child});

  final Map<String, Object> _claims = <String, Object>{};

  /// True when [owner] holds the mark for [term]. Idempotent: the same owner
  /// asking twice — which is what a rebuild is — gets the same answer.
  bool claim(String term, Object owner) {
    final Object? held = _claims[term];
    if (held == null) {
      _claims[term] = owner;
      return true;
    }
    return identical(held, owner);
  }

  static GlossaryScope? maybeOf(BuildContext context) =>
      context.dependOnInheritedWidgetOfExactType<GlossaryScope>();

  @override
  bool updateShouldNotify(GlossaryScope oldWidget) => false;
}

class GlossaryText extends StatefulWidget {
  const GlossaryText(this.text, {super.key, required this.style});

  final String text;
  final TextStyle style;

  @override
  State<GlossaryText> createState() => _GlossaryTextState();
}

class _GlossaryTextState extends State<GlossaryText> {
  @override
  Widget build(BuildContext context) {
    final GlossaryScope? scope = GlossaryScope.maybeOf(context);
    final List<InlineSpan> spans =
        _spans(context, widget.text, widget.style, scope, this);

    // No terms found: a plain Text, so the common case costs nothing and stays
    // selectable and searchable like any other label.
    if (spans.length == 1 && spans.first is TextSpan &&
        (spans.first as TextSpan).children == null) {
      return Text(widget.text, style: widget.style);
    }
    return Text.rich(TextSpan(style: widget.style, children: spans));
  }
}

List<InlineSpan> _spans(
  BuildContext context,
  String text,
  TextStyle style,
  GlossaryScope? scope,
  Object owner,
) {
  final List<InlineSpan> out = <InlineSpan>[];
  final String lower = text.toLowerCase();
  int cursor = 0;

  while (cursor < text.length) {
    ({int at, String form})? hit;

    for (final String form in kGlossaryForms) {
      final int at = lower.indexOf(form, cursor);
      if (at < 0) continue;
      // Whole words only: "variants" must not match inside "invariant", and
      // "position" must not match inside "positioning".
      if (at > 0 && _isWordChar(text[at - 1])) continue;
      final int end = at + form.length;
      if (end < text.length && _isWordChar(text[end])) continue;
      if (hit == null || at < hit.at || (at == hit.at && form.length > hit.form.length)) {
        hit = (at: at, form: form);
      }
    }

    if (hit == null) {
      out.add(TextSpan(text: text.substring(cursor)));
      break;
    }

    final GlossaryTerm term = kGlossaryByForm[hit.form]!;
    // Claim per canonical term, not per spelling: "metabolizer" and
    // "metaboliser" are the same word twice, and marking both would be exactly
    // the repetition first-use-only exists to avoid.
    final bool mark = scope?.claim(term.term, owner) ?? true;

    if (hit.at > cursor) {
      out.add(TextSpan(text: text.substring(cursor, hit.at)));
    }
    final String asWritten = text.substring(hit.at, hit.at + hit.form.length);

    if (mark) {
      out.add(WidgetSpan(
        alignment: PlaceholderAlignment.baseline,
        baseline: TextBaseline.alphabetic,
        child: _Term(word: asWritten, term: term, style: style),
      ));
    } else {
      out.add(TextSpan(text: asWritten));
    }
    cursor = hit.at + hit.form.length;
  }

  if (out.isEmpty) out.add(TextSpan(text: text));
  return out;
}

bool _isWordChar(String c) => RegExp(r'[A-Za-z0-9]').hasMatch(c);

class _Term extends StatelessWidget {
  const _Term({required this.word, required this.term, required this.style});

  final String word;
  final GlossaryTerm term;
  final TextStyle style;

  @override
  Widget build(BuildContext context) => Semantics(
    button: true,
    // Names the word AND says a definition is available. "poor metaboliser"
    // alone gives a screen-reader user no signal that this one is different
    // from the surrounding prose.
    label: '$word. Definition available.',
    excludeSemantics: true,
    child: InkWell(
      onTap: () => showGlossaryDefinition(context, term),
      focusColor: Tokens.accent.withValues(alpha: 0.28),
      borderRadius: Tokens.radius,
      child: Text(
        word,
        style: style.copyWith(
          // A dotted underline, not a colour change or a bold — the word has
          // to stay part of the sentence. Colour would read as a link out.
          decoration: TextDecoration.underline,
          decorationStyle: TextDecorationStyle.dotted,
          decorationColor: Tokens.ink3,
        ),
      ),
    ),
  );
}

/// A ticker with no parent to mute it. Needed only to drive a zero-length
/// controller; nothing here ever actually ticks.
class _PlainTicker implements TickerProvider {
  const _PlainTicker();

  @override
  Ticker createTicker(TickerCallback onTick) => Ticker(onTick);
}

/// Show one definition. A sheet rather than a dialog: it does not cover what
/// the reader was reading, which is the sentence that prompted the question.
///
/// Honours reduced motion. Flutter does not apply `disableAnimations` on a
/// widget's behalf — each animation has to check — and a sheet that slides up
/// is exactly the motion the setting exists to stop.
Future<void> showGlossaryDefinition(
    BuildContext context, GlossaryTerm term) async {
  final bool stillness = MediaQuery.disableAnimationsOf(context);
  final AnimationController? instant = stillness
      ? AnimationController(vsync: const _PlainTicker(), duration: Duration.zero)
      : null;

  await showModalBottomSheet<void>(
    context: context,
    transitionAnimationController: instant,
    backgroundColor: Tokens.card,
    shape: const RoundedRectangleBorder(
      borderRadius: BorderRadius.vertical(top: Radius.circular(6)),
    ),
    builder: (BuildContext context) => Semantics(
      namesRoute: true,
      // Without this the container's own label is merged away by the children
      // below it, and a screen reader announces the definition without ever
      // saying which word it belongs to.
      explicitChildNodes: true,
      label: 'Definition of ${term.term}',
      child: Padding(
        padding: const EdgeInsets.fromLTRB(18, 14, 18, 24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: <Widget>[
            Container(
              width: 34, height: 3,
              margin: const EdgeInsets.only(bottom: 14),
              color: Tokens.rule2,
            ),
            Text(term.term.toUpperCase(), style: Tokens.monoLabel),
            const SizedBox(height: 6),
            Text(term.definition, style: Tokens.prose),
            const SizedBox(height: 14),
            Align(
              alignment: Alignment.centerRight,
              child: TextButton(
                onPressed: () => Navigator.of(context).pop(),
                child: Text('Close', style: Tokens.uiMd),
              ),
            ),
          ],
        ),
      ),
    ),
  );
  instant?.dispose();
}
