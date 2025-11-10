import csv
import json
from typing import Any, cast, NotRequired, TypedDict

import click

from clingen_client import ClingenClient
from mavedb_client import MaveDBClient


class Keyword(TypedDict):
    key: str
    label: NotRequired[str]
    system: NotRequired[str]
    code: NotRequired[str]
    version: NotRequired[str]


class ExperimentKeyword(TypedDict):
    keyword: Keyword
    description: NotRequired[str]  # Additional details, e.g. for when the keyword is 'Other'


def can_detect_nmd_variants(score_set_urn: str, experiment_variant_library_creation_method: ExperimentKeyword | None) -> bool | None:
    """
    Can an experiment detect NMD variants?

    This is currently determined by looking at the library creation method, but there are two exceptions.
    """
    if experiment_variant_library_creation_method is None:
        return None
    if experiment_variant_library_creation_method .get("keyword", {}).get("label", None) == "Endogenous locus library method":
        return not score_set_urn.startswith("urn:mavedb:00001242")
    return score_set_urn.startswith("urn:mavedb:00001226")


def can_detect_splicing_variants(score_set_urn: str, experiment_variant_library_creation_method: ExperimentKeyword | None) -> bool | None:
    """
    Can an experiment detect splicing variants?

    This is currently determined by looking at the library creation method, but there is one exception.
    """
    if experiment_variant_library_creation_method is None:
        return None
    if experiment_variant_library_creation_method .get("keyword", {}).get("label", None) == "Endogenous locus library method":
        return True
    return score_set_urn.startswith("urn:mavedb:00001226")


def find_keyword(experiment_keywords: list[ExperimentKeyword], key: str):
    return next((keyword for keyword in experiment_keywords if keyword.get("keyword", {}).get("key", None) == key), None)


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
    results: list[dict[str, Any]] = []

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

                    experiment = score_set.get("experiment")
                    if experiment is None:
                        raise(Exception(f"Missing experiment for variant {hgvs} (URN {variant_urn})."))

                    primary_publications = score_set.get("primaryPublicationIdentifiers", [])
                    primary_publication = primary_publications[0] if primary_publications else None
                    variant_effect_measurement_source_db = cast(str | None, primary_publication.get("dbName", None)) if primary_publication else None
                    variant_effect_measurement_source_identifier = cast(str | None, primary_publication.get("identifier", None)) if primary_publication else None
                    variant_effect_measurement_source_authors = primary_publication.get("authors", []) if primary_publication else []
                    variant_effect_measurement_source_first_author = next((author for author in variant_effect_measurement_source_authors if author.get("primary", False)), None)
                    variant_effect_measurement_source_first_author_name = cast(str | None, variant_effect_measurement_source_first_author.get("name", None)) if variant_effect_measurement_source_first_author else None
                    variant_effect_measurement_source_publication_year = cast(int | None, primary_publication.get("publicationYear", None)) if primary_publication else None
                    variant_effect_measurement_source_publication_journal = cast(str | None, primary_publication.get("publicationJournal", None)) if primary_publication else None

                    experiment_keywords = experiment.get("keywords", [])
                    experiment_variant_library_creation_method = find_keyword(experiment_keywords, "Variant Library Creation Method")
                    experiment_endogenous_locus_library_method_system = find_keyword(experiment_keywords, "Endogenous Locus Library Method System")
                    experiment_endogenous_locus_library_method_mechanism = find_keyword(experiment_keywords, "Endogenous Locus Library Method Mechanism")
                    experiment_in_vitro_construct_library_method_system = find_keyword(experiment_keywords, "In Vitro Construct Library Method System")
                    experiment_in_vitro_construct_library_method_mechanism = find_keyword(experiment_keywords, "In Vitro Construct Library Method Mechanism")
                    experiment_delivery_method = find_keyword(experiment_keywords, "Delivery method")
                    experiment_phenotypic_assay_dimensionality = find_keyword(experiment_keywords, "Phenotypic Assay Dimensionality")
                    experiment_phenotypic_assay_method = find_keyword(experiment_keywords, "Phenotypic Assay Method")
                    experiment_phentypic_assay_mechanism = find_keyword(experiment_keywords, "Phenotypic Assay Mechanism")
                    experiment_molecular_mechanism_assessed = find_keyword(experiment_keywords, "Molecular Mechanism Assessed")
                    experiment_phenotypic_assay_model_system = find_keyword(experiment_keywords, "Phenotypic Assay Model System")
                    experiment_phenotypic_assay_profiling_strategy = find_keyword(experiment_keywords, "Phenotypic Assay Profiling Strategy")
                    experiment_phenotypic_assay_sequencing_read_type = find_keyword(experiment_keywords, "Phenotypic Assay Sequencing Read Type")

                    experiment_detects_nmd_variants = can_detect_nmd_variants(score_set_urn, experiment_variant_library_creation_method)
                    experiment_detects_splicing_variants = can_detect_splicing_variants(score_set_urn, experiment_variant_library_creation_method)

                    score_range_label: str | None = None
                    score_range_classification: str | None = None
                    score_range_min: float | None = None
                    score_range_max: float | None = None
                    odds_path: float | None = None
                    acmg_evidence_strength: str | None = None
                    calibration_source_db: str | None = None
                    calibration_source_identifier: str | None = None
                    evidence_strength_source_db: str | None = None
                    evidence_strength_source_identifier: str | None = None

                    if score is not None:
                        # TODO The data model for calibrations will change in MaveDB v2025.5.0.
                        calibrations = score_set.get("scoreRanges")

                        # Get the primary calibration. MaveDB v2025.5.0 will tell us which one is primary, but for now
                        # we prioritize Scott, CVFG (all variants), and investigator-provided calibrations, in that
                        # order. If a primary calibration is flagged for research use only, ignore it.
                        primary_calibration = calibrations.get("scottCalibration", calibrations.get("cvfgAllVariants", calibrations.get("investigatorProvided", None)))
                        if primary_calibration.get("researchUseOnly", False):
                            primary_calibration = None

                        if primary_calibration:
                            for range in primary_calibration.get("ranges", []):
                                if score_lies_in_range(score, range):
                                    score_range_label = cast(str | None, range.get("label", None))
                                    score_range_classification = cast(str | None, range.get("classification", None))
                                    score_range_min = cast(float | None, range.get("range", [None, None])[0])
                                    score_range_max = cast(float | None, range.get("range", [None, None])[1])
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
                            "variant_urn": variant_urn,

                            "score": score,
                            "score_data": json.dumps(score_data),
                            "count_data": json.dumps(count_data) if count_data else None,

                            "score_range_label": score_range_label,
                            "score_range_classification": score_range_classification,
                            "score_range_min": score_range_min,
                            "score_range_max": score_range_max,
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

                            "score_set_urn": score_set_urn,
                            "score_set_title": score_set.get("title", None),
                            "score_set_short_description": score_set.get("shortDescription", None),
                            "score_set_published_date": score_set.get("publishedDate", None),

                            "experiment_urn": experiment.get("urn", None),
                            "experiment_title": experiment.get("title", None),
                            "experiment_short_description": experiment.get("shortDescription", None),

                            # Controlled keywords
                            "experiment_variant_library_creation_method_label": experiment_variant_library_creation_method.get("keyword", {}).get("label", None) if experiment_variant_library_creation_method else None,
                            "experiment_variant_library_creation_method_description": experiment_variant_library_creation_method.get("description", None) if experiment_variant_library_creation_method else None,
                            "experiment_endogenous_locus_library_method_system_label": experiment_endogenous_locus_library_method_system.get("keyword", {}).get("label", None) if experiment_endogenous_locus_library_method_system else None,
                            "experiment_endogenous_locus_library_method_system_description": experiment_endogenous_locus_library_method_system.get("description", None) if experiment_endogenous_locus_library_method_system else None,
                            "experiment_endogenous_locus_library_method_mechanism_label": experiment_endogenous_locus_library_method_mechanism.get("keyword", {}).get("label", None) if experiment_endogenous_locus_library_method_mechanism else None,
                            "experiment_endogenous_locus_library_method_mechanism_description": experiment_endogenous_locus_library_method_mechanism.get("description", None) if experiment_endogenous_locus_library_method_mechanism else None,
                            "experiment_in_vitro_construct_library_method_system_label": experiment_in_vitro_construct_library_method_system.get("keyword", {}).get("label", None) if experiment_in_vitro_construct_library_method_system else None,
                            "experiment_in_vitro_construct_library_method_system_description": experiment_in_vitro_construct_library_method_system.get("description", None) if experiment_in_vitro_construct_library_method_system else None,
                            "experiment_in_vitro_construct_library_method_mechanism_label": experiment_in_vitro_construct_library_method_mechanism.get("keyword", {}).get("label", None) if experiment_in_vitro_construct_library_method_mechanism else None,
                            "experiment_in_vitro_construct_library_method_mechanism_description": experiment_in_vitro_construct_library_method_mechanism.get("description", None) if experiment_in_vitro_construct_library_method_mechanism else None,
                            "experiment_delivery_method_label": experiment_delivery_method.get("keyword", {}).get("label", None) if experiment_delivery_method else None,
                            "experiment_delivery_method_description": experiment_delivery_method.get("description", None) if experiment_delivery_method else None,
                            "experiment_phenotypic_assay_dimensionality_label": experiment_phenotypic_assay_dimensionality.get("keyword", {}).get("label", None) if experiment_phenotypic_assay_dimensionality else None,
                            "experiment_phenotypic_assay_dimensionality_description": experiment_phenotypic_assay_dimensionality.get("description", None) if experiment_phenotypic_assay_dimensionality else None,
                            "experiment_phenotypic_assay_method_label": experiment_phenotypic_assay_method.get("keyword", {}).get("label", None) if experiment_phenotypic_assay_method else None,
                            "experiment_phenotypic_assay_method_description": experiment_phenotypic_assay_method.get("description", None) if experiment_phenotypic_assay_method else None,
                            "experiment_phentypic_assay_mechanism_label": experiment_phentypic_assay_mechanism.get("keyword", {}).get("label", None) if experiment_phentypic_assay_mechanism else None,
                            "experiment_phentypic_assay_mechanism_description": experiment_phentypic_assay_mechanism.get("description", None) if experiment_phentypic_assay_mechanism else None,
                            "experiment_molecular_mechanism_assessed_label": experiment_molecular_mechanism_assessed.get("keyword", {}).get("label", None) if experiment_molecular_mechanism_assessed else None,
                            "experiment_molecular_mechanism_assessed_description": experiment_molecular_mechanism_assessed.get("description", None) if experiment_molecular_mechanism_assessed else None,
                            "experiment_phenotypic_assay_model_system_label": experiment_phenotypic_assay_model_system.get("keyword", {}).get("label", None) if experiment_phenotypic_assay_model_system else None,
                            "experiment_phenotypic_assay_model_system_description": experiment_phenotypic_assay_model_system.get("description", None) if experiment_phenotypic_assay_model_system else None,
                            "experiment_phenotypic_assay_profiling_strategy_label": experiment_phenotypic_assay_profiling_strategy.get("keyword", {}).get("label", None) if experiment_phenotypic_assay_profiling_strategy else None,
                            "experiment_phenotypic_assay_profiling_strategy_description": experiment_phenotypic_assay_profiling_strategy.get("description", None) if experiment_phenotypic_assay_profiling_strategy else None,
                            "experiment_phenotypic_assay_sequencing_read_type_label": experiment_phenotypic_assay_sequencing_read_type.get("keyword", {}).get("label", None) if experiment_phenotypic_assay_sequencing_read_type else None,
                            "experiment_phenotypic_assay_sequencing_read_type_description": experiment_phenotypic_assay_sequencing_read_type.get("description", None) if experiment_phenotypic_assay_sequencing_read_type else None,

                            "experiment_detects_nmd_variants": experiment_detects_nmd_variants,
                            "experiment_detects_splicing_variants": experiment_detects_splicing_variants,
                        })

    with open(output_csv, mode='w', newline='') as outfile:
        fieldnames = [
            "hgvs",
            "clingen_allele_id",
            "variant_urn",
            "score",
            "score_data",
            "count_data",

            "score_range_min",
            "score_range_max",
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

            "score_set_urn",
            "score_set_title",
            "score_set_short_description",
            "score_set_published_date",

            "experiment_urn",
            "experiment_title",
            "experiment_short_description",
            
            "experiment_variant_library_creation_method_label",
            "experiment_variant_library_creation_method_description",
            "experiment_endogenous_locus_library_method_system_label",
            "experiment_endogenous_locus_library_method_system_description",
            "experiment_endogenous_locus_library_method_mechanism_label",
            "experiment_endogenous_locus_library_method_mechanism_description",
            "experiment_in_vitro_construct_library_method_system_label",
            "experiment_in_vitro_construct_library_method_system_description",
            "experiment_in_vitro_construct_library_method_mechanism_label",
            "experiment_in_vitro_construct_library_method_mechanism_description",
            "experiment_delivery_method_label",
            "experiment_delivery_method_description",
            "experiment_phenotypic_assay_dimensionality_label",
            "experiment_phenotypic_assay_dimensionality_description",
            "experiment_phenotypic_assay_method_label",
            "experiment_phenotypic_assay_method_description",
            "experiment_phentypic_assay_mechanism_label",
            "experiment_phentypic_assay_mechanism_description",
            "experiment_molecular_mechanism_assessed_label",
            "experiment_molecular_mechanism_assessed_description",
            "experiment_phenotypic_assay_model_system_label",
            "experiment_phenotypic_assay_model_system_description",
            "experiment_phenotypic_assay_profiling_strategy_label",
            "experiment_phenotypic_assay_profiling_strategy_description",
            "experiment_phenotypic_assay_sequencing_read_type_label",
            "experiment_phenotypic_assay_sequencing_read_type_description",

            "experiment_detects_nmd_variants",
            "experiment_detects_splicing_variants",
        ]
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

if __name__ == "__main__":
    main()
