# MaveDB Variant Lookup

This project provides a tool for looking up genetic variants in [MaveDB](https://mavedb.org/). It processes a CSV file containing HGVS strings, retrieves relevant data from the MaveDB API, and outputs the results into a new CSV file.

The HGVS search is reference-independent, to the same extent as ClinGen Allele Registry searches.

One row is returned for each variant measurement matching one of the searches. The row includes information about the variant, the individual measurement, and the score set to which it belongs. In addition, if the score set containing a measurement has a primary calibration that is not marked "research use only," the row includes details of the score range into which the variant falls, as well as OddsPath and ACMG evidence strength if available.

## Project Structure

```
mavedb-variant-lookup
├── src
│   ├── mavedb_lookup.py       # Main script for processing variants
│   ├── clingen_client.py      # API client for ClinGen interactions
│   └── mavedb_client.py       # API client for MaveDB interactions
├── pyproject.toml             # Project configuration
├── requirements.txt           # Project dependencies for pip
└── README.md                  # Project documentation
```

## Installation

To set up the project, clone the repository and install the required dependencies:

```bash
git clone <repository-url>
cd mavedb-variant-lookup
pip install -r requirements.txt
```

### Using Poetry

This is the preferred installation method. `pyproject.toml` configures Poetry and specifies dependencies.

Install Poetry if it is not already installed. See the [official Poetry documentation](https://python-poetry.org/docs/#installation). One way to install Poetry is to first install `pipx` (see the [pipx documentation](https://pipx.pypa.io/stable/installation/)), then use it to install Poetry:

```bash
pipx install poetry
```

Now use Poetry to create a Python virtual environment and install dependencies:

```bash
poetry env use
poetry install
```

### Using pip

A `requirements.txt` file is also provided that specifies the same dependencies, in case you prefer to use `pip` directly.

First activate your virtual environment, unless you want to install dependencies globally (which is not recommended). In our example, the virtual environment has already been created at `./.venv`:

```bash
source .venv/bin/activate
```

Now install the dependencies:

```bash
pip install
```

## Usage

To run the variant lookup, execute the main script with the input CSV file containing HGVS strings:

```bash
python src/mavedb_lookup.py <input_file.csv> <output_file.csv>
```

- `<input_file.csv>`: Path to the input CSV file with a column named `hgvs`.
- `<output_file.csv>`: Path where the output CSV file will be saved.

## Limitations

Only data about the requested variant are returned; related protein or DNA variants are not considered. Thus, if a DNA variant is requested, only MAVE scores describing the same DNA variant are returned, even if MAVE scores exist that describe the variant's protein consequence or other DNA variants that are coding-equivalent. Similarly, if a protein variant is requested, MAVE scores describing DNA variants that produce the specified protein change are not returned. In the future, we may add an option to include data about related variants.

Multi-variants (including haplotypes) are not currently supported, but the MaveDB website's search capabilities allow searching for multi-variants.

## Output

The output CSV file will contain one row for each variant effect measurement stored in MaveDB that matches one of the requested variants. If multiple experiments or score sets describe one of the requested variants, this variant will be described by multiple rows of the output; if MaveDB contains no measurement describing a variant, the output will contain no rows describing that variant.

The output has the following columns:

- hgvs: The requested HGVS string.
- clingen_allele_id: The ClinGen allele ID of this variant.
- variant_urn: The variant measurement's URN, which serves as an unique identifier in MaveDB.
- score: The variant measurement score.
- score_data: A JSON string containing the score and any other score-related columns uploaded by the investigator.
- count_data: A JSON string containing any count-related columns uploaded by the investigator.
- score_range_label: The investigator-supplied name of the score range. Empty if the score does not lie in any range.
- score_range_classification: A functional classification of the score range. Empty if the score does not lie in any range or its range does not have a functional classification.
- score_range_min: The minimum value of the range containing the score (empty if the range begins at negative infinity). Empty if the score does not lie in any range.
- score_range_max: The maximum value of the range containing the score (empty if the range ends at negative infinity). Empty if the score does not lie in any range.
- odds_path: Odds of pathogenicity (OddsPath) for variants in this range, as calculated by the investigator or calibrator. Empty if the score does not lie in any range or its range does not have a calculated OddsPath.
- acmg_evidence_strength: An ACMG evidence strength code for variants in this range, as calculated by the investigator or calibrator. Empty if the score does not lie in any range or its range does not have an evidence strength code.
- variant_effect_measurement_source_db: Publication database (often PubMed, bioRxiv, or Crossref) for the primary publication associated with this score set.
- variant_effect_measurement_source_identifier: Publication identifier for the primary publication associated with this score set, in the database specified by variant_effect_measurement_source_db.
- variant_effect_measurement_source_first_author: First author of the primary publication associated with this score set.
- variant_effect_measurement_source_publication_year: Year of publication of the primary publication associated with this score set.
- variant_effect_measurement_source_publication_journal: Journal of the primary publication associated with this score set.
- calibration_source_db: Publication database (often PubMed, bioRxiv, or Crossref) for the primary publication in which the calibration used here (in the score_range columns) was provided.
- calibration_source_identifier: Publication identifier for the primary publication in which the calibration used here (in the score_range columns) was provided.
- evidence_strength_source_db: Publication database (often PubMed, bioRxiv, or Crossref) for the primary publication in which odds_path and/or acmg_evidence_strength were provided.
- evidence_strength_source_identifier: Publication identifier (often PubMed, bioRxiv, or Crossref) for the primary publication in which odds_path and/or acmg_evidence_strength were provided.
- score_set_urn: The MaveDB URN of the score set containing the measurement.
- score_set_title: The title the score set containing the measurement.
- score_set_short_description: A short description of the score set containing the measurement.
- score_set_publication_date: The publication date in MaveDB of the score set containing the measurement.
- experiment_urn: The MaveDB URN of the experiment.
- experiment_title: The title the experiment.
- experiment_short_description: A short description of the experiment.
- experiment_variant_library_creation_method_label: A keyword identifying the variant library creation method of the experiment.
- experiment_variant_library_creation_method_description: Additional details describing the variant library creation method of the experiment.
- experiment_endogenous_locus_library_method_system_label: A keyword identifying the endogenous locus library method system of the experiment.
- experiment_endogenous_locus_library_method_system_description: Additional details describing the endogenous locus library method system of the experiment.
- experiment_endogenous_locus_library_method_mechanism_label: A keyword identifying the endogenous locus library method mechanism of the experiment.
- experiment_endogenous_locus_library_method_mechanism_description: Additional details describing the endogenous locus library method mechanism of the experiment.
- experiment_in_vitro_construct_library_method_system_label: A keyword identifying the in vitro construct library method system of the experiment.
- experiment_in_vitro_construct_library_method_system_description: Additional details describing the in vitro construct library method system of the experiment.
- experiment_in_vitro_construct_library_method_mechanism_label: A keyword identifying the in vitro construct library method mechanism of the experiment.
- experiment_in_vitro_construct_library_method_mechanism_description: Additional details describing the in vitro construct library method mechanism of the experiment.
- experiment_delivery_method_label: A keyword identifying the delivery method of the experiment.
- experiment_delivery_method_description: Additional details describing the delivery method of the experiment.
- experiment_phenotypic_assay_dimensionality_label: A keyword identifying the phenotypic assay dimensionality of the experiment.
- experiment_phenotypic_assay_dimensionality_description: Additional details describing the phenotypic assay dimensionality of the experiment.
- experiment_phenotypic_assay_method_label: A keyword identifying the phenotypic assay method of the experiment.
- experiment_phenotypic_assay_method_description: Additional details describing the phenotypic assay method of the experiment.
- experiment_phentypic_assay_mechanism_label: A keyword identifying the phentypic assay mechanism of the experiment.
- experiment_phentypic_assay_mechanism_description: Additional details describing the phentypic assay mechanism of the experiment.
- experiment_molecular_mechanism_assessed_label: A keyword identifying the molecular mechanism assessed of the experiment.
- experiment_molecular_mechanism_assessed_description: Additional details describing the molecular mechanism assessed of the experiment.
- experiment_phenotypic_assay_model_system_label: A keyword identifying the phenotypic assay model system of the experiment.
- experiment_phenotypic_assay_model_system_description: Additional details describing the phenotypic assay model system of the experiment.
- experiment_phenotypic_assay_profiling_strategy_label: A keyword identifying the phenotypic assay profiling strategy of the experiment.
- experiment_phenotypic_assay_profiling_strategy_description: Additional details describing the phenotypic assay profiling strategy of the experiment.
- experiment_phenotypic_assay_sequencing_read_type_label: A keyword identifying the phenotypic assay sequencing read type of the experiment.
- experiment_phenotypic_assay_sequencing_read_type_description: Additional details describing the phenotypic assay sequencing read type of the experiment.
- experiment_detects_nmd_variants: A boolean flag indicating whether the experiment can detect NMD variants. Empty if unknown..
- experiment_detects_splicing_variants: A boolean flag indicating whether the experiment can detect splicing variants. Empty if unknown..

## Example

Given an input CSV file with the following content:

```
hgvs
NP_000242.1:p.Val161Asp
NC_000014.9:g.90404488A>T
```

The output might look like:

```csv
hgvs,clingen_allele_id,variant_urn,score,score_data,count_data,score_range_min,score_range_max,score_range_label,score_range_classification,odds_path,acmg_evidence_strength,variant_effect_measurement_source_db,variant_effect_measurement_source_identifier,variant_effect_measurement_source_first_author,variant_effect_measurement_source_publication_year,variant_effect_measurement_source_publication_journal,calibration_source_db,calibration_source_identifier,evidence_strength_source_db,evidence_strength_source_identifier,score_set_urn,score_set_title,score_set_short_description,score_set_published_date,experiment_urn,experiment_title,experiment_short_description,experiment_variant_library_creation_method_label,experiment_variant_library_creation_method_description,experiment_endogenous_locus_library_method_system_label,experiment_endogenous_locus_library_method_system_description,experiment_endogenous_locus_library_method_mechanism_label,experiment_endogenous_locus_library_method_mechanism_description,experiment_in_vitro_construct_library_method_system_label,experiment_in_vitro_construct_library_method_system_description,experiment_in_vitro_construct_library_method_mechanism_label,experiment_in_vitro_construct_library_method_mechanism_description,experiment_delivery_method_label,experiment_delivery_method_description,experiment_phenotypic_assay_dimensionality_label,experiment_phenotypic_assay_dimensionality_description,experiment_phenotypic_assay_method_label,experiment_phenotypic_assay_method_description,experiment_phentypic_assay_mechanism_label,experiment_phentypic_assay_mechanism_description,experiment_molecular_mechanism_assessed_label,experiment_molecular_mechanism_assessed_description,experiment_phenotypic_assay_model_system_label,experiment_phenotypic_assay_model_system_description,experiment_phenotypic_assay_profiling_strategy_label,experiment_phenotypic_assay_profiling_strategy_description,experiment_phenotypic_assay_sequencing_read_type_label,experiment_phenotypic_assay_sequencing_read_type_description,experiment_detects_nmd_variants,experiment_detects_splicing_variants
NP_000242.1:p.Val161Asp,PA095173,urn:mavedb:00000050-a-1#3046,2.3985129910466934,"{""score"": 2.3985129910466934, ""mavedb_clnsig"": ""Pathogenic"", ""mavedb_clnrevstat"": ""reviewed_by_expert_panel""}",,0.0,,Loss of function,abnormal,,,PubMed,33357406,Jia X,2021,Am J Hum Genet,PubMed,31892348,,,urn:mavedb:00000050-a-1,MSH2 LOF scores (HAP1),MSH2 loss-of-function (LOF) scores in human HAP1 cells.,2020-11-25,urn:mavedb:00000050-a,MSH2 deep mutational scan,Massively parallel functional testing of MSH2 missense variants conferring Lynch Syndrome risk,In vitro construct library method,,,,,,Oligo-directed mutagenic PCR,,Random locus viral integration,,Lentivirus transduction,,Single-dimensional data,,Cell fitness,,Loss of function,,DNA and Mismatch repair,,Immortalized human cells,Homo sapiens (NCBI:txid9606),Barcode sequencing,,Single-segment (short read),,False,False
NC_000014.9:g.90404488A>T,CA390690357,urn:mavedb:00000001-c-1#4824,0.812210121634973,"{""sd"": 0.0387012345952488, ""se"": 0.0193506172976244, ""score"": 0.812210121634973}",,,,,,,,PubMed,29269382,"Weile, Jochen",2017,Mol Syst Biol,,,,,urn:mavedb:00000001-c-1,Human Calmodulin DMS-TileSeq,A Deep Mutational Scan of human Calmodulin using functional complementation in yeast via DMS-TileSeq.,2018-06-29,urn:mavedb:00000001-c,Calmodulin yeast complementation,A Deep Mutational Scan of human Calmodulin using functional complementation in yeast.,In vitro construct library method,,,,,,Oligo-directed mutagenic PCR,POPCode (Precision Oligo-Pool based Code Alteration),Plasmid (not integrated),,Chemical-based transfection,,Single-dimensional data,,Cell fitness,,Loss of function,,Calcium-mediated signaling,,Yeast,Saccharomyces cerevisiae (NCBI:txid4932),Direct sequencing,,Single-segment (short read),,False,False
```

## Development notes

MaveDB v2025.5.0 (forthcoming) includes calibration data model changes such as
- An explicitly identified primary calibration for each score set
- An additional source citation describing the evidence strength method, which is distinct from the source citation for the evidence strength calculation
- And support for evidence strengths without OddsPath.

This project will be updated accordingly. Because more score calibrations will be available once MaveDB v2025.5.0 is released, users of this project may want to wait for the update.

## License

This project is licensed under the GNU Affero General Public License. See the LICENSE file for more details.
