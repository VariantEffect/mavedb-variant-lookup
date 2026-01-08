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
                allele = clingen_data[0] if len(clingen_data) > 0 else None
            else:
                allele = clingen_data

        except requests.RequestException as e:
            allele = None

        return allele

    def fetch_clingen_allele_ids(self, hgvs: str):
        """
        A ClinGen allele resource has a (partial) structure like this example:

        ```
        {
          "@context": "http://reg.genome.network/schema/allele.jsonld",
          "@id": "http://reg.genome.network/allele/CA034588",
          "transcriptAlleles": [
            "MANE": {
              "maneVersion": "1.3",
              "maneStatus": "MANE Select",
              "nucleotide": {
                "Ensembl": {
                  "hgvs": "ENST00000233146.7:c.2197G>A"
                },
                "RefSeq": {
                  "hgvs": "NM_000251.3:c.2197G>A"
                }
              },
              "protein": {
                "Ensembl": {
                  "hgvs": "ENSP00000233146.2:p.Ala733Thr"
                },
                "RefSeq": {
                  "hgvs": "NP_000242.1:p.Ala733Thr"
                }
              }
            }
          }
        }
        ```

        :param self: Description
        :param hgvs: Description
        """
        allele = self.fetch_clingen_allele(hgvs)

        allele_ids = {
            "exact": None,
            "mane": [],
            "related_protein": [],
            "related_dna": [],
        }
        if allele:
            exact_allele_id = self.get_clingen_allele_id(allele)
            allele_ids["exact"] = exact_allele_id

            transcript_alleles = allele.get("transcriptAlleles")
            if exact_allele_id and transcript_alleles:
                for transcript_allele in transcript_alleles:
                    mane = transcript_allele.get("MANE")
                    if mane:
                        for sequence_type in ["nucleotide", "protein"]:
                            for database in mane[sequence_type]:
                                allele_set = "mane"
                                if (
                                    exact_allele_id.startswith("C")
                                    and sequence_type == "protein"
                                ):
                                    allele_set = "related_protein"
                                if (
                                    exact_allele_id.startswith("P")
                                    and sequence_type == "nucleotide"
                                ):
                                    allele_set = "related_dna"
                                hgvs = mane[sequence_type][database]["hgvs"]
                                related_allele_hgvs = self.fetch_clingen_allele(hgvs)
                                if related_allele_hgvs:
                                    related_allele_id = self.get_clingen_allele_id(
                                        related_allele_hgvs
                                    )
                                    if related_allele_id:
                                        allele_ids[allele_set].append(related_allele_id)
        allele_ids["mane"] = list(set(allele_ids["mane"]))
        allele_ids["related_dna"] = list(set(allele_ids["related_dna"]))
        allele_ids["related_protein"] = list(set(allele_ids["related_protein"]))
        allele_ids["mane"] = [
            id for id in set(allele_ids["mane"]) if id != allele_ids["exact"]
        ]
        allele_ids["related_dna"] = [
            id
            for id in set(allele_ids["related_dna"])
            if id != allele_ids["exact"] and not id in allele_ids["mane"]
        ]
        allele_ids["related_protein"] = [
            id
            for id in set(allele_ids["related_protein"])
            if id != allele_ids["exact"] and not id in allele_ids["mane"]
        ]

        return allele_ids

    def get_clingen_allele_id(self, allele: Any):
        allele_id = allele.get("@id")
        if allele_id is not None:
            allele_id = str(allele_id).split("/")[-1]
            if allele_id in ["_:CA", "_:PA"]:
                return None
            return allele_id
        return None
