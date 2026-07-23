/// The persistent "this is not a medical device" banner.
///
/// Shown on every screen, always visible, never dismissible. The whole project
/// is an academic prototype serving fabricated values; nothing about the UI
/// should let a passing reader forget that.
library;

import 'package:flutter/material.dart';

import '../config.dart';

class DisclaimerBanner extends StatelessWidget {
  const DisclaimerBanner({super.key});

  @override
  Widget build(BuildContext context) {
    final ThemeData theme = Theme.of(context);
    final bool dark = theme.brightness == Brightness.dark;
    final Color bg = dark
        ? const Color(0xFF4A3B12)
        : const Color(0xFFFFF4CE);
    final Color fg = dark
        ? const Color(0xFFF7E6B8)
        : const Color(0xFF5C4400);

    return Material(
      color: bg,
      child: SafeArea(
        top: false,
        bottom: false,
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: <Widget>[
              Icon(Icons.info_outline, size: 18, color: fg),
              const SizedBox(width: 10),
              Expanded(
                child: Text(
                  kDisclaimer,
                  style: theme.textTheme.bodySmall?.copyWith(
                    color: fg,
                    fontWeight: FontWeight.w600,
                    height: 1.35,
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

/// Scaffold wrapper that pins [DisclaimerBanner] beneath the app bar on every
/// screen, so no screen can accidentally ship without it.
class BannerScaffold extends StatelessWidget {
  const BannerScaffold({
    super.key,
    required this.appBar,
    required this.body,
    this.floatingActionButton,
  });

  final PreferredSizeWidget appBar;
  final Widget body;
  final Widget? floatingActionButton;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: appBar,
      floatingActionButton: floatingActionButton,
      body: Column(
        children: <Widget>[
          const DisclaimerBanner(),
          Expanded(child: body),
        ],
      ),
    );
  }
}
