import unittest

from app.routes.legacy_formatter import gold_to_legacy


class LegacyFormatterTest(unittest.TestCase):
    def test_converts_gold_payload(self) -> None:
        payload = {
            "brands": [
                {
                    "items": [
                        {
                            "brand": "Starbucks",
                            "productName": "Latte",
                            "size": "TALL",
                            "beverageType": "ESPRESSO",
                            "nutrition": {"servingKcal": 100},
                        },
                        {
                            "brand": "Starbucks",
                            "productName": "Latte",
                            "size": "VENTI",
                            "beverageType": "ESPRESSO",
                            "nutrition": {"servingKcal": 200},
                        },
                    ]
                },
                {
                    "items": [
                        {
                            "brand": "MegaCoffee",
                            "productName": "Mega Latte",
                            "size": "MEGA",
                            "beverageType": "COFFEE",
                            "nutrition": {"servingKcal": 300},
                        }
                    ]
                },
            ]
        }
        legacy = gold_to_legacy(payload)
        self.assertEqual(len(legacy), 2)
        starbucks = next(item for item in legacy if item["brand"] == "STARBUCKS")
        self.assertEqual(set(starbucks["beverageNutritions"].keys()), {"TALL", "VENTI"})
        megacoffee = next(item for item in legacy if item["brand"] == "MEGA_COFFEE")
        self.assertEqual(len(megacoffee["beverageNutritions"]), 1)
        self.assertEqual(megacoffee["beverageNutritions"][0]["size"], "MEGA")

    def test_filters_by_brand(self) -> None:
        payload = {
            "brands": [
                {
                    "items": [
                        {
                            "brand": "Starbucks",
                            "productName": "Latte",
                            "size": "TALL",
                            "beverageType": "ESPRESSO",
                            "nutrition": {"servingKcal": 100},
                        }
                    ]
                }
            ]
        }
        legacy = gold_to_legacy(payload, brand_filter="megacoffee")
        self.assertEqual(len(legacy), 0)


if __name__ == "__main__":
    unittest.main()
