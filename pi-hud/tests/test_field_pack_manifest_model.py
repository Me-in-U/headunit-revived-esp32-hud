from __future__ import annotations

import unittest

from hud_pi.field_pack_manifest_model import FIELD_PACK_KIND, FIELD_PACK_SCHEMA_VERSION, PayloadEntry


class FieldPackManifestModelTest(unittest.TestCase):
    def test_manifest_model_preserves_kind_schema_and_payload_entry_contract(self) -> None:
        entry = PayloadEntry("layouts/test.json", b"{}", source="layout.json")

        self.assertEqual("headunit-pi-field-pack", FIELD_PACK_KIND)
        self.assertEqual(1, FIELD_PACK_SCHEMA_VERSION)
        self.assertEqual("layouts/test.json", entry.path)
        self.assertEqual(b"{}", entry.payload)
        self.assertEqual("layout.json", entry.source)


if __name__ == "__main__":
    unittest.main()
