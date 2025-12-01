from typing import Any
from urllib.parse import quote

import requests


class ClingenClient:
    def __init__(self, base_url="https://reg.clinicalgenome.org"):
        self.base_url = base_url

    def fetch_clingen_allele(self, hgvs: str) -> Any:
        # resolve HGVS to a ClinGen Allele Registry ID, then query MaveDB by that ID
        try:
            response = requests.get(
                f"{self.base_url}/allele?hgvs={quote(hgvs, safe='')}",
                timeout=10,
            )
            response.raise_for_status()
            clingen_data = response.json()
            # print(json.dumps(clingen_data, indent=2))

            # Support either object or list responses. If the response was a list, only look at the first element.
            if isinstance(clingen_data, list):
                alleles = clingen_data
            else:
                alleles = [clingen_data]

        except requests.RequestException as e:
            alleles = []

        return alleles

    def get_exact_match_clingen_allele_ids(self, alleles: list[Any]):
        allele_ids = []
        for allele in alleles:
            allele_id = allele.get("@id")
            if allele_id is not None:
                allele_id = str(allele_id).split("/")[-1]
                allele_ids.append(allele_id)
        return allele_ids
