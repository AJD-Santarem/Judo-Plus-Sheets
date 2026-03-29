from config import Config
import os
import yaml

# =====================================================
# HELPERS: LOAD YAML
# =====================================================

def load_grouped_yaml(file_path):
    """
    Load a grouped athletes YAML file.
    Returns a dict or {} if missing/empty.
    """
    if not os.path.exists(file_path):
        print(f"Warning: file not found -> {file_path}")
        return {}

    with open(file_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    return data if data else {}


# =====================================================
# HELPERS: EXTRACT GROUPS
# =====================================================

def extract_groups_from_yaml(grouped_data, sex_label):
    """
    Flatten grouped YAML structure into a list of group objects.

    Input structure expected:
    {
      AGE_TIER: {
        WEIGHT_CLASS: {
          Group1: [...],
          Group2: [...],
          Ungrouped: [...]
        }
      }
    }

    We extract only GroupX entries and ignore Ungrouped.
    """
    groups = []

    for age_tier, weight_classes in grouped_data.items():
        if not isinstance(weight_classes, dict):
            continue

        for weight_class, groups_dict in weight_classes.items():
            if not isinstance(groups_dict, dict):
                continue

            for group_name, athletes in groups_dict.items():
                if not str(group_name).startswith("Group"):
                    continue

                if not isinstance(athletes, list) or len(athletes) == 0:
                    continue

                # Convert Group1 -> G1
                group_short = group_name.replace("Group", "")

                # Display label example: -60 G1
                sex_short = "M" if sex_label.startswith("M") else "F"
                age_tier_short = abbreviate_age_tier(age_tier)
                display_label = f"{sex_short} {age_tier_short} {weight_class} {group_short}" 

                groups.append({
                    "Sex": sex_label,
                    "Sex Short": sex_short,
                    "Age Tier": age_tier,
                    "Age Tier Short": age_tier_short,
                    "Weight Class": weight_class,
                    "Group Name": group_name,
                    "Group Short": group_short,
                    "Display Label": display_label,
                    "Group Size": len(athletes)
                })

    return groups


# =====================================================
# HELPERS: DISTRIBUTE TO MATS
# =====================================================

def distribute_groups_to_mats(groups, number_of_mats):
    """
    Distribute groups across mats as evenly as possible by athlete load.

    Strategy:
    - Sort groups by size descending
    - Assign each group to the mat with the lowest current athlete load
    - Tie-breaker: lower number of groups
    """
    if number_of_mats <= 0:
        raise ValueError("number_of_mats must be >= 1")

    mats = [
        {
            "Mat Number": i + 1,
            "Mat": f"Mat {i+1}",
            "Total Groups": 0,
            "Total Athletes": 0,
            "Groups": []
        }
        for i in range(number_of_mats)
    ]

    groups_sorted = sorted(groups, key=lambda g: g["Group Size"], reverse=True)

    for group in groups_sorted:
        target_mat = min(
            mats,
            key=lambda m: (m["Total Athletes"], m["Total Groups"])
        )

        target_mat["Groups"].append(group)
        target_mat["Total Groups"] += 1
        target_mat["Total Athletes"] += group["Group Size"]

    return mats


# =====================================================
# HELPERS: EXPORT YAML
# =====================================================

def export_mat_distribution_yaml(mats, stage, output_file):
    """
    Export mat distribution to YAML.

    Output contains:
    - summary metadata
    - Assignments (flat list, best for Excel lookup)
    - Mats (grouped by mat, useful for inspection/debugging)
    """
    total_groups = sum(mat["Total Groups"] for mat in mats)
    total_athletes = sum(mat["Total Athletes"] for mat in mats)

    assignments = []
    mats_output = []

    for mat in mats:
        mat_number = mat["Mat Number"]
        mat_label = mat["Mat"]

        mat_group_labels = []

        for group in mat["Groups"]:
            assignments.append({
                "MatNumber": mat_number,
                "Sex": group["Sex"],
                "AgeTier": group["Age Tier"],
                "AgeTierShort": group["Age Tier Short"],
                "WeightClass": group["Weight Class"],
                "GroupName": group["Group Name"],
                "GroupNumber": group["Group Short"],
                "GroupSize": group["Group Size"],
            })

            mat_group_labels.append(group["Display Label"])

        mats_output.append({
            "MatNumber": mat_number,
            "TotalGroups": mat["Total Groups"],
            "TotalAthletes": mat["Total Athletes"],
            "Groups": mat_group_labels
        })

    output_data = {
        "Stage": stage,
        "NumberOfMats": len(mats),
        "TotalGroups": total_groups,
        "TotalAthletes": total_athletes,
        "Assignments": assignments,
        "Mats": mats_output
    }

    with open(output_file, "w", encoding="utf-8") as f:
        yaml.safe_dump(
            output_data,
            f,
            allow_unicode=True,
            sort_keys=False
        )

    print(f"Mat distribution YAML saved to {output_file}")


# =====================================================
# HELPERS: AGE TIER ABBREVIATION
# =====================================================

def age_tier_prefix(tier_name):
    """
    Short prefix used in mat labels.
    """
    prefix_map = {
        "Benjamim": "B",
        "Infantil": "Inf",
        "Iniciado": "Ini"
    }

    return prefix_map.get(tier_name, tier_name[:3])

def build_age_tier_abbrev_map(age_rules):
    """
    Build a mapping like:
    {
        "Benjamim (2017–2018)": "B17/18",
        "Benjamim (2015–2016)": "B15/16",
        "Infantil (2014)": "Inf",
        "Iniciado (2013)": "Ini"
    }
    """
    abbrev_map = {}

    for tier_name, rules in age_rules.items():
        prefix = age_tier_prefix(tier_name)

        for rule in rules:
            label = rule["label"]
            years = rule["years"]

            # Use last 2 digits of each year
            year_parts = [str(y)[-2:] for y in years]

            if len(year_parts) == 1:
                year_part = year_parts[0]
            else:
                year_part = "/".join(year_parts)

            abbrev_map[label] = f"{prefix}{year_part}"

    return abbrev_map

def abbreviate_age_tier(age_tier):
    """
    Convert full AGE_TIER labels into compact mat-table labels.
    """
    if not age_tier:
        return ""

    normalized = str(age_tier).replace("-", "–").strip()
    return build_age_tier_abbrev_map(Config.AGE_RULES).get(normalized, normalized)


# =====================================================
# MAIN
# =====================================================

def run_mat_distribution(stage, number_of_mats):
    """
    1) Load grouped YAMLs for the selected stage
    2) Extract actual groups
    3) Combine male + female groups
    4) Distribute across mats
    5) Export markdown table
    """
    male_data = load_grouped_yaml(Config.male_grouped_file())
    female_data = load_grouped_yaml(Config.female_grouped_file())

    male_groups = extract_groups_from_yaml(male_data, Config.MALE)
    female_groups = extract_groups_from_yaml(female_data, Config.FEMALE)

    all_groups = male_groups + female_groups

    if not all_groups:
        print(f"No valid groups found for stage {stage}.")
        return []

    mats = distribute_groups_to_mats(all_groups, number_of_mats)

    export_mat_distribution_yaml(mats, stage, Config.mat_distribution_yaml())

    return mats


if __name__ == "__main__":
    run_mat_distribution(Config.STAGE, Config.NUMBER_OF_MATS)