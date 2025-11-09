import csv
import json
from typing import Any, cast

import click

from clingen_client import ClingenClient
from mavedb_client import MaveDBClient


def score_lies_in_range(score: float, range: Any):
    score_range = range.get("range", None)
    if score_range is None:
        return False
    inclusive_lower_bound = cast(bool, range.get("inclusiveLowerBound", False))
    inclusive_upper_bound = cast(bool, range.get("inclusiveUpperBound", False))
    range_min = cast(float | None, score_range[0])
    range_max = cast(float | None, score_range[1])
    if inclusive_lower_bound:
        if range_min is not None and score < range_min:
            return False
    else:
        if range_min is not None and score <= range_min:
            return False
    if inclusive_upper_bound:
        if range_max is not None and score > range_max:
            return False
    else:
        if range_max is not None and score >= range_max:
            return False
    return True


@click.command()
@click.argument("input_csv")
@click.argument("output_csv")
def main(input_csv: str, output_csv: str):
    clingen_client = ClingenClient()
    mavedb_client = MaveDBClient()
    results = []

    with open(input_csv, mode='r') as infile:
        reader = csv.DictReader(infile)

    
        for row in reader:
            hgvs = row['hgvs']
            clingen_alleles = clingen_client.fetch_clingen_allele(hgvs)
            clingen_allele_ids = clingen_client.get_exact_match_clingen_allele_ids(clingen_alleles)
            if (not clingen_allele_ids):
                raise(Exception(f"No allele ID for {hgvs}"))
            for clingen_allele_id in clingen_allele_ids:
                variant_effect_measurements = mavedb_client.fetch_variant_effect_measurements(clingen_allele_id)
                # print(json.dumps(variant_effect_measurements, indent=2))

                for variant_effect_measurement in variant_effect_measurements:
                    variant_urn = cast(str, variant_effect_measurement.get("urn"))
                    score_data = variant_effect_measurement.get("data", {}).get("score_data", {})
                    count_data = variant_effect_measurement.get("data", {}).get("count_data", {})
                    score = cast(float | None, score_data.get("score", None))
                    score_set_urn = cast(str, variant_effect_measurement.get("scoreSet").get("urn"))

                    score_set = mavedb_client.fetch_score_set(score_set_urn)
                    if score_set is None:
                        raise(Exception(f"Missing score set for variant {hgvs} (URN {variant_urn})."))

                    primary_publications = score_set.get("primaryPublicationIdentifiers", [])
                    primary_publication = primary_publications[0] if primary_publications else None
                    variant_effect_measurement_source_db = cast(str | None, primary_publication.get("dbName", None)) if primary_publication else None
                    variant_effect_measurement_source_identifier = cast(str | None, primary_publication.get("identifier", None)) if primary_publication else None
                    variant_effect_measurement_source_authors = primary_publication.get("authors", []) if primary_publication else []
                    variant_effect_measurement_source_first_author = next((author for author in variant_effect_measurement_source_authors if author.get("primary", False)), None)
                    variant_effect_measurement_source_first_author_name = cast(str | None, variant_effect_measurement_source_first_author.get("name", None)) if variant_effect_measurement_source_first_author else None
                    variant_effect_measurement_source_publication_year = cast(int | None, primary_publication.get("publicationYear", None)) if primary_publication else None
                    variant_effect_measurement_source_publication_journal = cast(str | None, primary_publication.get("publicationJournal", None)) if primary_publication else None

                    score_range_label: str | None = None
                    score_range_classification: str | None = None
                    odds_path: float | None = None
                    acmg_evidence_strength: str | None = None
                    calibration_source_db: str | None = None
                    calibration_source_identifier: str | None = None
                    odds_path_source_db: str | None = None
                    odds_path_source_identifier: str | None = None

                    if score is not None:
                        # TODO The data model for calibrations will change in MaveDB v2025.5.0.
                        calibrations = score_set.get("scoreRanges")
                        primary_calibration = calibrations.get("scottCalibration", calibrations.get("cvfgAllVariants", calibrations.get("investigatorProvided", None)))
                        if primary_calibration.get("researchUseOnly", False):
                            primary_calibration = None
                        if primary_calibration:
                            for range in primary_calibration.get("ranges", []):
                                if score_lies_in_range(score, range):
                                    score_range_label = cast(str | None, range.get("label", None))
                                    score_range_classification = cast(str | None, range.get("classification", None))
                                    odds_path = cast(float | None, range.get("oddsPath", {}).get("ratio", None))
                                    acmg_evidence_strength = cast(str | None, range.get("oddsPath", {}).get("evidence", None))
                                    calibration_sources = primary_calibration.get("source", [])
                                    calibration_source = calibration_sources[0] if calibration_sources else {}
                                    calibration_source_db = calibration_source.get("dbName", None)
                                    calibration_source_identifier = calibration_source.get("identifier", None)
                                    odds_path_sources = primary_calibration.get("odssPathSource", [])
                                    odds_path_source = odds_path_sources[0] if odds_path_sources else {}
                                    evidence_strength_source_db = odds_path_source.get("dbName", None)
                                    evidence_strength_source_identifier = odds_path_source.get("identifier", None)
                                    break

                        results.append({
                            "hgvs": hgvs,
                            "clingen_allele_id": clingen_allele_id,
                            "mavedb_variant_urn": variant_urn,
                            "mavedb_score_set_urn": score_set_urn,
                            "score": score,
                            "score_data": json.dumps(score_data),
                            "count_data": json.dumps(count_data) if count_data else None,
                            "score_range_label": score_range_label,
                            "score_range_classification": score_range_classification,
                            "odds_path": odds_path,
                            "acmg_evidence_strength": acmg_evidence_strength,
                            "variant_effect_measurement_source_db": variant_effect_measurement_source_db,
                            "variant_effect_measurement_source_identifier": variant_effect_measurement_source_identifier,
                            "variant_effect_measurement_source_first_author": variant_effect_measurement_source_first_author_name,
                            "variant_effect_measurement_source_publication_year": variant_effect_measurement_source_publication_year,
                            "variant_effect_measurement_source_publication_journal": variant_effect_measurement_source_publication_journal,
                            "calibration_source_db": calibration_source_db,
                            "calibration_source_identifier": calibration_source_identifier,
                            "evidence_strength_source_db": evidence_strength_source_db,
                            "evidence_strength_source_identifier": evidence_strength_source_identifier,
                        })

    with open(output_csv, mode='w', newline='') as outfile:
        fieldnames = [
            "hgvs",
            "clingen_allele_id",
            "mavedb_variant_urn",
            "mavedb_score_set_urn",
            "score",
            "score_data",
            "count_data",
            "score_range_label",
            "score_range_classification",
            "odds_path",
            "acmg_evidence_strength",
            "variant_effect_measurement_source_db",
            "variant_effect_measurement_source_identifier",
            "variant_effect_measurement_source_first_author",
            "variant_effect_measurement_source_publication_year",
            "variant_effect_measurement_source_publication_journal",
            "calibration_source_db",
            "calibration_source_identifier",
            "evidence_strength_source_db",
            "evidence_strength_source_identifier",
        ]
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

if __name__ == "__main__":
    main()
