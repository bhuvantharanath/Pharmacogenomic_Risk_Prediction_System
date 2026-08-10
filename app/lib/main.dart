/// PharmaGuard — Flutter client (web + Android/iOS from this one codebase).
///
/// A thin rendering layer over the backend's JSON contract: it computes no
/// clinical value of its own. Diplotypes and phenotypes come from PharmCAT and
/// all recommendation text is CPIC's, copied verbatim; the client's job is to
/// display them, colour-code the risk, and keep the disclaimer visible.
library;

import 'package:flutter/material.dart';

import 'screens/home_screen.dart';
import 'theme/tokens.dart';

void main() => runApp(const PharmaGuardApp());

class PharmaGuardApp extends StatelessWidget {
  const PharmaGuardApp({super.key});

  /// Deliberately clinical/neutral rather than red or green — the card colours
  /// carry the risk signal, and the chrome should not compete with them.

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      theme: Tokens.theme(),
      title: 'PharmaGuard',
      debugShowCheckedModeBanner: false,
      home: const HomeScreen(),
    );
  }

}
