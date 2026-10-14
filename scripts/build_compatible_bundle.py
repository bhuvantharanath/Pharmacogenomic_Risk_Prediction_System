#!/usr/bin/env python3
"""Regenerate the compatible scientific-bundle manifest after a controlled upgrade."""

from __future__ import annotations

import json

from compatible_bundle import MANIFEST_PATH, build_manifest


if __name__ == "__main__":
    MANIFEST_PATH.write_text(json.dumps(build_manifest(), indent=2) + "\n")
    print(MANIFEST_PATH)
