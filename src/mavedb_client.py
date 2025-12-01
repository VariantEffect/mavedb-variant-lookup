import requests


class MaveDBClient:
    def __init__(self, base_url="https://api.mavedb.org/api/v1"):
        self.base_url = base_url

    def fetch_score_set(self, urn: str):
        response = requests.get(f"{self.base_url}/score-sets/{urn}")
        if response.status_code == 404:
            return None
        response.raise_for_status()
        return response.json()

    def fetch_variant_effect_measurements(self, clingen_allele_id: str):
        response = requests.post(
            f"{self.base_url}/variants/clingen-allele-id-lookups",
            json={"clingenAlleleIds": [clingen_allele_id]},
        )
        if response.status_code == 404:
            return []
        response.raise_for_status()
        variants = response.json()
        if not isinstance(variants, list):
            raise TypeError("Expected JSON response to be a list")
        if not variants:
            return []
        first_variant = variants[0]
        if not isinstance(first_variant, dict):
            raise TypeError("Expected first array element to be an object")
        return (first_variant.get("exactMatch", {}) or {}).get(
            "variantEffectMeasurements", []
        )
