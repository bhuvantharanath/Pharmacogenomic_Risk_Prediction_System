/// A status or error message that a screen reader can name and announce.
///
/// The app shows these messages with [SelectableText], so a person can copy an
/// error and send it on. Flutter exposes selectable text as a *textbox*, and
/// A8 found the 503 busy message announced as an unlabelled textbox: the
/// listener hears that there is an editable field, not what it says or that
/// anything has gone wrong.
///
/// This replaces the subtree's semantics with one named, read-only node, and
/// marks it a live region so it is announced when it appears rather than only
/// when focus happens to land on it. The visible text and its selectability
/// are unchanged.
///
/// The trade: with `excludeSemantics` the inner textbox's own selection
/// semantics go away, so a screen reader no longer offers text-selection
/// gestures over the message. That is the right way round — an unlabelled
/// editable field that cannot be identified is worse than a named message that
/// cannot be selected by gesture, and the text is still selectable by pointer.
library;

import 'package:flutter/material.dart';

class MessageText extends StatelessWidget {
  const MessageText(
    this.message, {
    super.key,
    this.style,
    this.kind,
    this.liveRegion = true,
  });

  final String message;
  final TextStyle? style;

  /// Spoken before the message to say what kind of message it is, e.g.
  /// 'Error' or 'Server status'. A message that reads as a plain sentence
  /// gives no clue that it is a failure.
  final String? kind;

  /// False for a message that is always on screen, which would otherwise be
  /// re-announced on every rebuild.
  final bool liveRegion;

  /// What a screen reader says for [message] of this [kind].
  static String nameFor(String message, String? kind) =>
      kind == null || kind.isEmpty ? message : '$kind. $message';

  @override
  Widget build(BuildContext context) => Semantics(
    container: true,
    liveRegion: liveRegion,
    readOnly: true,
    label: nameFor(message, kind),
    excludeSemantics: true,
    child: SelectableText(message, style: style),
  );
}
