/// A tap-to-open row. The app's only disclosure idiom.
///
/// WHY IT REPLACED `ExpansionTile`
///
/// Two reasons, and the second is the load-bearing one.
///
/// `ExpansionTile` animates its open and close, and offers no way to switch
/// that off. Flutter does not disable implicit animations for a user who has
/// asked their system for reduced motion — `MediaQuery.disableAnimations` is a
/// flag each widget has to honour, and Material's expansion tile does not
/// expose the hook. A row that simply appears has no animation to suppress, so
/// the requirement is met by construction rather than by a setting.
///
/// It is also the same control everywhere: the verdict card, the readiness
/// panel and the coverage summary all disclose the same way, so learning it
/// once is enough.
library;

import 'package:flutter/material.dart';

import '../theme/tokens.dart';

class DisclosureRow extends StatefulWidget {
  const DisclosureRow({
    super.key,
    required this.title,
    required this.child,
    this.subtitle,
    this.leading,
    this.padding = const EdgeInsets.fromLTRB(14, 12, 14, 12),
    this.rule = true,
  });

  final String title;
  final String? subtitle;
  final Widget? leading;
  final Widget child;
  final EdgeInsets padding;

  /// Hairline under the row. Off when the caller draws its own boundary.
  final bool rule;

  @override
  State<DisclosureRow> createState() => _DisclosureRowState();
}

class _DisclosureRowState extends State<DisclosureRow> {
  bool _open = false;

  @override
  Widget build(BuildContext context) => Column(
    crossAxisAlignment: CrossAxisAlignment.stretch,
    children: <Widget>[
      Semantics(
        button: true,
        expanded: _open,
        label: widget.subtitle == null
            ? widget.title
            : '${widget.title}. ${widget.subtitle}',
        excludeSemantics: true,
        child: InkWell(
          onTap: () => setState(() => _open = !_open),
          // Focus has to be visible: this is the control a keyboard user lands
          // on most often, and the default ripple is invisible on paper.
          focusColor: Tokens.accent.withValues(alpha: 0.28),
          child: Padding(
            padding: widget.padding,
            child: Row(
              children: <Widget>[
                if (widget.leading != null) ...<Widget>[
                  widget.leading!,
                  const SizedBox(width: 10),
                ],
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: <Widget>[
                      Text(widget.title,
                          style: Tokens.uiMd
                              .copyWith(fontWeight: FontWeight.w600)),
                      if (widget.subtitle != null) ...<Widget>[
                        const SizedBox(height: 2),
                        Text(widget.subtitle!, style: Tokens.uiSm),
                      ],
                    ],
                  ),
                ),
                Icon(_open ? Icons.remove : Icons.add,
                    size: 17, color: Tokens.ink3),
              ],
            ),
          ),
        ),
      ),
      if (_open)
        Padding(
          padding: EdgeInsets.fromLTRB(
              widget.padding.left, 0, widget.padding.right, 14),
          child: widget.child,
        ),
      if (widget.rule) Container(height: Tokens.hairline, color: Tokens.rule),
    ],
  );
}
