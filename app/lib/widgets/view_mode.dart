/// Two registers over one set of facts.
///
/// WHAT THIS IS NOT
///
/// It is NOT two versions of the truth. The same fields are rendered in both
/// views, from the same response, with the same words — what changes is which
/// of them you meet first and which wait behind a disclosure row. Nothing is
/// added for one audience and nothing is withheld from the other.
///
/// That constraint is deliberate and worth stating, because the obvious version
/// of this feature is the wrong one: generating "simpler" text for patients
/// would mean a second body of clinical prose that no guard checks and no
/// adjudication covers. Every clinical sentence in this system is machine-traced
/// to a CPIC recommendation. A patient-friendly rewrite would be a sentence with
/// no source, shown to the reader least equipped to notice.
///
/// So the toggle reorders. Nothing more.
///
/// WHAT STAYS PUT IN BOTH
///
/// The coverage census and the disclaimer. A reader in either register needs to
/// know what was not checked and that this is not a medical device, and a view
/// that hid either would be a view that lied by omission.
///
/// SESSION ONLY
///
/// Held in memory, not on disk. A clinician's preference on a shared demo
/// machine should not greet the next person, and a stored default would make
/// "patient view" stop being the thing a first-time visitor sees.
library;

import 'package:flutter/foundation.dart';

enum ViewMode {
  /// Default. Prose first; the machine detail is one tap away.
  patient('For a patient', 'Plain language first'),

  /// Genotype, evidence level and CPIC's own words, immediately.
  clinician('For a clinician', 'Genotype and guideline first');

  const ViewMode(this.label, this.hint);

  final String label;
  final String hint;

  ViewMode get other => this == patient ? clinician : patient;
}

/// The session's choice. A plain notifier rather than an InheritedWidget: the
/// value has to survive a Navigator push to About and back, and it is read from
/// widgets that are not all under one subtree.
final ValueNotifier<ViewMode> viewMode = ValueNotifier<ViewMode>(ViewMode.patient);

/// Reset between tests. Session state that leaked across tests would make the
/// default-is-patient assertion pass or fail depending on test order.
@visibleForTesting
void resetViewMode() => viewMode.value = ViewMode.patient;
