# config.py
import base64
import os
import random


class Config:
    """
    Central configuration class for the tournament system.

    This class defines:
    - Tournament metadata
    - File paths
    - Weight class rules
    - Age grouping rules
    - Utility helpers (paths, RNG, encoding)

    All values are accessed statically via class attributes or methods.
    """

    # =====================================================
    # TOURNAMENT METADATA
    # =====================================================

    ORG_NAME = "Associação de Judo do Distrito de Santarém"
    """Name of the organizing entity displayed in reports and PDFs."""

    STAGE = "I"
    """
    Tournament stage.

    Values:
    - "B" → Benjamins
    - "I" → Iniciados / Infantis
    """

    TOURNAMENT_CODE = "REPLACE_WITH_UNIQUE_CODE"
    """Unique identifier for the tournament used in file structure and outputs."""


    LOC_DATE = "Location, date"
    """Location and date string shown in generated outputs."""


    NUMBER_OF_MATS = 5
    """Number of mats (tatamis) available for the competition."""

    RANDOM_SEED = 21
    """
    Seed used for deterministic randomness.

    Set to None for non-deterministic execution.
    """

    # =====================================================
    # TEMPLATE FILES
    # =====================================================

    TEMPLATE_BO3 = "Resources/Templates/BO_3.xlsx"
    """Excel template for best-of-3 matches (2 athletes)."""

    TEMPLATE_5 = "Resources/Templates/Poule_5.xlsx"
    """Excel template for 5-athlete pools."""

    TEMPLATE_2X = "Resources/Templates/2x_poule.xlsx"
    """Excel template for double-pool formats."""

    TABLE_FILES_FOLDER = "Resources/Templates/Table"
    """Directory containing HTML/CSS templates for PDF generation."""

    TABLE_TEMPLATE_FILE = "mat_distribution.html"
    """HTML template used to generate mat distribution PDF."""

    ORG_LOGO = "Resources/ORG_LOGO.png"
    """Path to organization logo used in reports."""

    # =====================================================
    # OUTPUT NAMING
    # =====================================================

    EXCEL_PATTERN = "{age_tier_short}_{sex}_{group_number}_{weight_class}.xlsx"
    """
    Filename pattern for generated Excel sheets.

    Placeholders:
    - age_tier_short
    - sex
    - group_number
    - weight_class
    """

    MALE = "Male"
    FEMALE = "Female"
    """Gender labels used throughout the system."""

    # =====================================================
    # WEIGHT CLASSES
    # =====================================================

    MASC_BINS = [0, 22, 26, 30, 34, 38, 42, 46, 50, 55, 60, 66, 73, float("inf")]
    MASC_LABELS = ["-22", "-26", "-30", "-34", "-38", "-42", "-46", "-50", "-55", "-60", "-66", "-73", "+73"]
    """
    Male weight classes.

    - Bins define numeric boundaries
    - Labels define category names
    """

    FEM_BINS = [0, 24, 28, 32, 36, 40, 44, 48, 52, 57, 63, 70, float("inf")]
    FEM_LABELS = ["-24", "-28", "-32", "-36", "-40", "-44", "-48", "-52", "-57", "-63", "-70", "+70"]
    """Female weight classes."""

    # =====================================================
    # AGE RULES
    # =====================================================

    AGE_RULES = {
        "Benjamim": [
            {"years": [2018, 2019], "label": "Benjamim (2018–2019)"},
            {"years": [2016, 2017], "label": "Benjamim (2016–2017)"}
        ],
        "Infantil": [
            {"years": [2015], "label": "Infantil (2015)"}
        ],
        "Iniciado": [
            {"years": [2014], "label": "Iniciado (2014)"}
        ]
    }
    """
    Mapping of age tiers to birth-year groups.

    Structure:
        {
            "TierName": [
                {
                    "years": [int],
                    "label": str
                }
            ]
        }
    """

    # =====================================================
    # TIER MAP (NORMALIZATION)
    # =====================================================

    TIER_MAP = {
        "benjamim": "Benjamim",
        "benjamins": "Benjamim",
        "infantil": "Infantil",
        "infantis": "Infantil",
        "iniciado": "Iniciado",
        "iniciados": "Iniciado"
    }
    """
    Mapping of age tiers to normalized names.

    Structure:
        {
            "tier_name": "Normalized Tier Name"
        }
    """

    # =====================================================
    # PATH HELPERS
    # =====================================================

    @classmethod
    def aux_output_folder(cls) -> str:
        """
        Get path to auxiliary output folder.

        Stores:
        - YAML files
        - PDFs
        - intermediate outputs

        :return: Path to auxiliary output directory
        :rtype: str
        """
        return os.path.join("Output", cls.TOURNAMENT_CODE, "Auxiliary_Files")

    @classmethod
    def excel_output_folder(cls) -> str:
        """
        Get path to Excel output folder.

        :return: Path to Excel output directory
        :rtype: str
        """
        return os.path.join("Output", cls.TOURNAMENT_CODE, "Excel_Sheets")

    @classmethod
    def table_css_file(cls) -> str:
        """
        Get path to CSS file for HTML table styling.

        :return: Path to CSS file
        :rtype: str
        """
        return os.path.join(cls.TABLE_FILES_FOLDER, "styles.css")

    # =====================================================
    # LOGO HANDLING
    # =====================================================

    @classmethod
    def get_logo_base64(cls) -> str:
        """
        Encode organization logo as Base64 data URI.

        Used to embed images in HTML/PDF without file path issues.

        :return: Base64 image string (data URI format)
        :rtype: str
        """
        with open(cls.ORG_LOGO, "rb") as f:
            encoded = base64.b64encode(f.read()).decode("utf-8")
            return f"data:image/png;base64,{encoded}"

    # =====================================================
    # STAGE HELPERS
    # =====================================================

    @classmethod
    def stage_label(cls) -> str:
        """
        Get human-readable label for tournament stage.

        :return: Stage label
        :rtype: str
        """
        if cls.STAGE == "B":
            return "Benjamins"
        elif cls.STAGE == "I":
            return "Iniciados/Infantis"
        return cls.STAGE

    # =====================================================
    # OUTPUT FILES
    # =====================================================

    @classmethod
    def male_grouped_file(cls) -> str:
        """
        Path to male grouped athletes YAML file.

        :return: File path
        :rtype: str
        """
        return os.path.join(cls.aux_output_folder(), f"{cls.STAGE}_Male_grouped_athletes.yaml")

    @classmethod
    def female_grouped_file(cls) -> str:
        """
        Path to female grouped athletes YAML file.

        :return: File path
        :rtype: str
        """
        return os.path.join(cls.aux_output_folder(), f"{cls.STAGE}_Female_grouped_athletes.yaml")

    @classmethod
    def mat_distribution_yaml(cls) -> str:
        """
        Path to mat distribution YAML file.

        :return: File path
        :rtype: str
        """
        return os.path.join(cls.aux_output_folder(), f"{cls.STAGE}_mat_distribution.yaml")

    @classmethod
    def mat_distribution_pdf(cls) -> str:
        """
        Path to generated mat distribution PDF.

        :return: File path
        :rtype: str
        """
        return os.path.join(cls.aux_output_folder(), f"{cls.STAGE}_mat_distribution.pdf")

    # =====================================================
    # RANDOM GENERATOR
    # =====================================================

    @classmethod
    def rng(cls) -> random.Random:
        """
        Get deterministic random generator instance.

        Uses RANDOM_SEED to ensure reproducibility.

        :return: Random number generator instance
        :rtype: random.Random
        """
        return random.Random(cls.RANDOM_SEED)