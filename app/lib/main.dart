/// PharmaGuard — Flutter client (web + Android/iOS from this one codebase).
///
/// A thin rendering layer over the backend's JSON contract: it computes no
/// clinical value of its own. Diplotypes and phenotypes come from PharmCAT and
/// all recommendation text is CPIC's, copied verbatim; the client's job is to
/// display them, colour-code the risk, and keep the disclaimer visible.
library;

import 'package:flutter/material.dart';

import 'screens/home_screen.dart';

void main() => runApp(const PharmaGuardApp());

class PharmaGuardApp extends StatelessWidget {
  const PharmaGuardApp({super.key});

  /// Deliberately clinical/neutral rather than red or green — the card colours
  /// carry the risk signal, and the chrome should not compete with them.
  static const Color _seed = Color(0xFF2A6F97);

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'PharmaGuard',
      debugShowCheckedModeBanner: false,
      theme: _theme(Brightness.light),
      darkTheme: _theme(Brightness.dark),
      // Follows the OS/browser setting; both modes are styled.
      themeMode: ThemeMode.system,
      home: const HomeScreen(),
    );
  }

  static ThemeData _theme(Brightness brightness) {
    final ColorScheme scheme = ColorScheme.fromSeed(
      seedColor: _seed,
      brightness: brightness,
    );
    return ThemeData(
      useMaterial3: true,
      colorScheme: scheme,
      appBarTheme: AppBarTheme(
        backgroundColor: scheme.surface,
        surfaceTintColor: scheme.surfaceTint,
        centerTitle: false,
        titleTextStyle: TextStyle(
          color: scheme.onSurface,
          fontSize: 20,
          fontWeight: FontWeight.w700,
        ),
        iconTheme: IconThemeData(color: scheme.onSurface),
      ),
      inputDecorationTheme: const InputDecorationTheme(
        border: OutlineInputBorder(),
      ),
    );
  }
}
