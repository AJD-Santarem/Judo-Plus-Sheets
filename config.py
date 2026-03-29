# config.py
import os
import random

class Config:
    TOURNAMENT_CODE = "TEST_CAT"

    LOC_DATE = "Location, date"

    STAGE = "B"  # B for first stage, "I" for the second stage

    NUMBER_OF_MATS = 5  # Adjust as needed

    RANDOM_SEED = 21  # Set to None for non-deterministic randomness

    # Define output folder for the generated sheet files
    EXCEL_OF = "Output/"

    TEMPLATE_BO3 = "Templates/BO_3.xlsx"
    TEMPLATE_5 = "Templates/Poule_5.xlsx"
    TEMPLATE_2X = "Templates/2x_poule.xlsx"

    EXCEL_PATTERN = "{age_tier_short}_{sex}_{group_number}_{weight_class}.xlsx"

    # File paths for the Excel templates
    BO3 = "Templates/BO_3.xlsx"
    POULE_5 = "Templates/Poule_5.xlsx"
    POULE_DOUBLE = "Templates/2x_poule.xlsx"  # Currently not used, but can be implemented for larger groups    
    
    MALE = "Male"
    FEMALE = "Female"

    # Fixed weight classes
    MASC_BINS = [0, 22, 26, 30, 34, 38, 42, 46, 50, 55, 60, 66, 73, float("inf")]
    MASC_LABELS = ["-22", "-26", "-30", "-34", "-38", "-42", "-46", "-50", "-55", "-60", "-66", "-73", "+73"]

    FEM_BINS = [0, 24, 28, 32, 36, 40, 44, 48, 52, 57, 63, 70, float("inf")]
    FEM_LABELS = ["-24", "-28", "-32", "-36", "-40", "-44", "-48", "-52", "-57", "-63", "-70", "+70"]

    AGE_RULES = {
        "Benjamim": [
            {"years": [2017, 2018], "label": "Benjamim (2017–2018)"},
            {"years": [2015, 2016], "label": "Benjamim (2015–2016)"}
        ],
        "Infantil": [
            {"years": [2014], "label": "Infantil (2014)"}
        ],
        "Iniciado": [
            {"years": [2013], "label": "Iniciado (2013)"}
        ]
    }

    @classmethod
    def output_folder(cls):
        return os.path.join("Output", cls.TOURNAMENT_CODE, "Auxiliary_Files")
    
    @classmethod
    def male_grouped_file(cls):
        return os.path.join(cls.output_folder(), f"{cls.STAGE}_Male_grouped_athletes.yaml")

    @classmethod
    def female_grouped_file(cls):
        return os.path.join(cls.output_folder(), f"{cls.STAGE}_Female_grouped_athletes.yaml")

    @classmethod
    def mat_distribution_yaml(cls):
        return os.path.join(cls.output_folder(), f"{cls.STAGE}_mat_distribution.yaml")

    @classmethod
    def rng(cls):
       return random.Random(cls.RANDOM_SEED)