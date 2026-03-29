from openpyxl import load_workbook
from config import Config
import yaml
import os

# =====================================================
# LOAD YAML
# =====================================================

def load_yaml(file_path, default=None):
    """
    Generic YAML loader.
    """
    if not os.path.exists(file_path):
        print(f"Warning: file not found -> {file_path}")
        return default if default is not None else {}

    with open(file_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    if data is None:
        return default if default is not None else {}

    return data


# =====================================================
# BUILD GROUP LOOKUP FROM GROUPED YAML
# =====================================================

def build_group_lookup(grouped_data, sex_label):
    """
    Build a lookup from grouped YAML:
    key = (Sex, AgeTier, WeightClass, GroupName)

    Example key:
    ("Male", "Benjamim (2017–2018)", "-38", "Group1")
    """
    lookup = {}

    if not isinstance(grouped_data, dict):
        return lookup

    for age_tier, weight_classes in grouped_data.items():
        if not isinstance(weight_classes, dict):
            continue

        for weight_class, groups_dict in weight_classes.items():
            if not isinstance(groups_dict, dict):
                continue

            for group_name, athletes in groups_dict.items():
                if not str(group_name).startswith("Group"):
                    continue

                if not isinstance(athletes, list):
                    athletes = []

                key = (sex_label, age_tier, weight_class, group_name)
                lookup[key] = athletes

    return lookup


def build_combined_group_lookup():
    """
    Load male + female grouped YAML and combine into a single lookup.
    """
    male_data = load_yaml(Config.male_grouped_file(), default={})
    female_data = load_yaml(Config.female_grouped_file(), default={})

    lookup = {}
    lookup.update(build_group_lookup(male_data, Config.MALE))
    lookup.update(build_group_lookup(female_data, Config.FEMALE))

    return lookup


# =====================================================
# POPULATE EXCEL
# =====================================================

def populate_group_table(group_data, athletes, template_file_2x, template_file_5, template_file_2, output_file_pattern):
    """
    Populate the correct Excel template using assignment info + athlete list.
    """
    group_size = group_data["GroupSize"]
    mat_number = group_data["MatNumber"]
    age_tier_full = group_data["AgeTier"]
    age_tier_short = group_data["AgeTierShort"].replace("/", "-")
    weight_class = group_data["WeightClass"]

    # Use GroupName from YAML (e.g. Group1)
    group_name = group_data["GroupName"]

    # Optional: display-friendly number/short label
    group_short = group_data.get("GroupShort", group_name.replace("Group", "G"))

    # Load appropriate template
    if group_size == 2:
        workbook = load_workbook(template_file_2)
        sheet = workbook.active

        sheet['F13'] = group_short.replace("G", "")
        sheet['G4'] = age_tier_full
        sheet['L4'] = str(weight_class) + " kg"
        sheet['L2'] = mat_number

        for i, athlete in enumerate(athletes, start=8):
            sheet[f'C{i}'] = athlete.get('Name', '')
            sheet[f'D{i}'] = str(athlete.get('Weight', '')) + " kg"
            sheet[f'E{i}'] = athlete.get('Club', '')

    elif 3 <= group_size <= 5:
        workbook = load_workbook(template_file_5)
        sheet = workbook.active

        sheet['M17'] = group_short.replace("G", "")
        sheet['K4'] = age_tier_full
        sheet['Q4'] = str(weight_class) + " kg"
        sheet['Q2'] = mat_number

        for i, athlete in enumerate(athletes, start=9):
            sheet[f'B{i}'] = athlete.get('Name', '')
            sheet[f'C{i}'] = str(athlete.get('Weight', '')) + " kg"
            sheet[f'D{i}'] = athlete.get('Club', '')

    else:  # 2X template for larger groups
        workbook = load_workbook(template_file_2x)
        sheet = workbook.active

        start_A = 8
        start_B = 24

        for i, athlete in enumerate(athletes):
            row = start_A + (i // 2) if i % 2 == 0 else start_B + (i // 2)
            sheet[f'B{row}'] = athlete.get('Name', '')
            sheet[f'C{row}'] = athlete.get('Weight', '')
            sheet[f'D{row}'] = athlete.get('Club', '')

        sheet['M2'] = mat_number
        sheet['M4'] = age_tier_full
        sheet['M6'] = group_short

    output_filename = os.path.join(
        Config.EXCEL_OF,
        output_file_pattern.format(
            age_tier_short=age_tier_short,
            sex=group_data["Sex"],
            group_number=group_short,
            weight_class=weight_class
        )
    )

    workbook.save(output_filename)
    print(f"{group_short} on mat {mat_number} saved to {output_filename}")


# =====================================================
# MAIN
# =====================================================

def generate_excel_from_yaml(yaml_file_path):
    """
    1) Load mat distribution YAML
    2) Load grouped athlete YAMLs
    3) For each assignment, fetch athletes from grouped lookup
    4) Populate correct Excel template
    """
    mat_data = load_yaml(yaml_file_path, default={})

    assignments = mat_data.get("Assignments", [])
    if not assignments:
        print("No assignments found in mat distribution YAML.")
        return

    group_lookup = build_combined_group_lookup()

    for group in assignments:
        key = (
            group["Sex"],
            group["AgeTier"],
            group["WeightClass"],
            group["GroupName"]
        )

        athletes = group_lookup.get(key, [])

        if not athletes:
            print(f"Warning: no athletes found for key={key}")

        populate_group_table(
            group_data=group,
            athletes=athletes,
            template_file_2x=Config.TEMPLATE_2X,
            template_file_5=Config.TEMPLATE_5,
            template_file_2=Config.TEMPLATE_BO3,
            output_file_pattern=Config.EXCEL_PATTERN
        )


if __name__ == "__main__":
    generate_excel_from_yaml(Config.mat_distribution_yaml())