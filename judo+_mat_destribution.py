from config import Config
from jinja2 import Environment, FileSystemLoader
import os
import yaml
import pdfkit

# =====================================================
# HELPERS: LOAD YAML
# =====================================================

def load_grouped_yaml(file_path):
    """
    Load a grouped athletes YAML file from disk.

    This is used as the input for mat distribution and expects a
    nested dictionary structure produced by the draw pipeline.

    :param file_path: Path to YAML file.
    :type file_path: str

    :return: Parsed YAML data or empty dict if file is missing/empty.
    :rtype: dict
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
    Flatten hierarchical YAML structure into a list of competition groups.

    Input structure:
    {
        AGE_TIER: {
            WEIGHT_CLASS: {
                GroupX: [athletes...],
                Ungrouped: [...]
            }
        }
    }

    Only valid GroupX entries are extracted. Ungrouped athletes are ignored.

    :param grouped_data: Nested YAML structure of grouped athletes.
    :type grouped_data: dict

    :param sex_label: Gender label ("Male" / "Female").
    :type sex_label: str

    :return: List of group dictionaries with metadata (size, label, etc.).
    :rtype: list[dict]
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
    Distribute competition groups across mats in a balanced way.

    Strategy:
    - Sort groups by size (descending)
    - Assign each group to the mat with lowest load
    - Avoid placing same weight class on the same mat when possible
    - Track total athletes and fights per mat

    Each group is enriched with:
    - calculated number of fights

    :param groups: List of competition groups.
    :type groups: list[dict]

    :param number_of_mats: Number of available mats (tatamis).
    :type number_of_mats: int

    :return: List of mats with assigned groups and statistics.
    :rtype: list[dict]
    """
    if number_of_mats <= 0:
        raise ValueError("number_of_mats must be >= 1")

    mats = [
        {
            "Mat Number": i + 1,
            "Mat": f"Mat {i+1}",
            "Total Groups": 0,
            "Total Athletes": 0,
            "Total Fights": 0,
            "Groups": []
        }
        for i in range(number_of_mats)
    ]

    groups_sorted = sorted(groups, key=lambda g: g["Group Size"], reverse=True)

    for group in groups_sorted:
        group_weight = group["Weight Class"]

        # Calculate fights
        group["Fights"] = calculate_fights(group["Group Size"])

        candidate_mats = [
            m for m in mats
            if all(g["Weight Class"] != group_weight for g in m["Groups"])
        ]

        # Try to avoid same weight in same mat
        if candidate_mats:
            target_mat = min(
                candidate_mats,
                key=lambda m: (m["Total Athletes"], m["Total Groups"])
            )
        else:
            target_mat = min(
                mats,
                key=lambda m: (m["Total Athletes"], m["Total Groups"])
            )

        target_mat["Groups"].append(group)
        target_mat["Total Groups"] += 1
        target_mat["Total Athletes"] += group["Group Size"]
        target_mat["Total Fights"] += group["Fights"]

        for mat in mats:
            mat["Groups"].sort(key=lambda g: g["Group Size"], reverse=True)

    return mats


# =====================================================
# HELPERS: EXPORT YAML
# =====================================================

def export_mat_distribution_yaml(mats, stage, output_file):
    """
    Export mat distribution results into a structured YAML file.

    The output contains:
    - metadata summary
    - flat assignment list (best for Excel processing)
    - mat-level grouping (best for inspection/debugging)

    :param mats: Mat assignment structure.
    :type mats: list[dict]

    :param stage: Tournament stage ("B" or "I").
    :type stage: str

    :param output_file: Destination YAML file path.
    :type output_file: str

    :return: None
    :rtype: None
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
# HELPERS: CALCULATE NUMBER OF FIGHTS
# =====================================================

def calculate_fights(group_size):
    """
    Calculate number of fights in a round-robin group.

    Formula:
        n(n - 1) / 2

    Special rule:
        - If group size == 2 → BO3 system (3 fights)

    :param group_size: Number of athletes in group.
    :type group_size: int

    :return: Number of fights in the group.
    :rtype: int
    """
    if group_size == 2:
        return 3  # special BO3 case
    return (group_size * (group_size - 1)) // 2


# =====================================================
# HELPERS: CREATE HTML TABLE
# =====================================================

def load_css():
    """
    Load CSS content used for HTML mat distribution rendering.

    This CSS is injected directly into the HTML template
    to ensure compatibility with wkhtmltopdf.

    :return: Raw CSS string.
    :rtype: str
    """
    with open(Config.table_css_file(), encoding="utf-8") as f:
        return f.read()

def render_mat_html(mats):
    """
    Render mat distribution into HTML using Jinja2 templates.

    This HTML is used as input for PDF generation via wkhtmltopdf.

    Features:
    - Injects tournament metadata
    - Embeds logo as base64
    - Applies CSS inline
    - Supports stage labeling

    :param mats: Mat assignment structure.
    :type mats: list[dict]

    :return: Fully rendered HTML string.
    :rtype: str
    """
    env = Environment(loader=FileSystemLoader(Config.TABLE_FILES_FOLDER))

    template = env.get_template(Config.TABLE_TEMPLATE_FILE)

    max_rows = max(len(mat["Groups"]) for mat in mats)

    html = template.render(
        mats=mats,
        max_rows=max_rows,
        loc_date=Config.LOC_DATE,
        org_name=Config.ORG_NAME,
        logo_path=Config.get_logo_base64(),
        css=load_css(),
        stage_label=Config.stage_label(),
        stage=Config.STAGE
    )

    #DEBUG: write HTML to file for inspection
    #with open(os.path.join(Config.aux_output_folder(), "debug.html"), "w", encoding="utf-8") as f:
    #    f.write(html)

    return html

def export_mat_distribution_pdf(mats, output_file):
    """
    Export mat distribution HTML into a PDF file.

    Uses wkhtmltopdf (via pdfkit) to render a print-ready document.

    :param mats: Mat assignment structure.
    :type mats: list[dict]

    :param output_file: Destination PDF path.
    :type output_file: str

    :return: None
    :rtype: None
    """
    html = render_mat_html(mats)

    pdfkit.from_string(
        html,
        output_file,
        options={
            "page-size": "A4",
            "orientation": "Landscape",
            "margin-top": "10mm",
            "margin-bottom": "10mm",
            "margin-left": "10mm",
            "margin-right": "10mm",
            "enable-local-file-access": None
        }
    )

    print(f"PDF saved to {output_file}")


# =====================================================
# HELPERS: AGE TIER ABBREVIATION
# =====================================================

def age_tier_prefix(tier_name):
    """
    Convert age tier name into a short prefix.

    Examples:
        Benjamim → B
        Infantil → Inf
        Iniciado → Ini

    :param tier_name: Full age tier name.
    :type tier_name: str

    :return: Short prefix.
    :rtype: str
    """
    prefix_map = {
        "Benjamim": "B",
        "Infantil": "Inf",
        "Iniciado": "Ini"
    }

    return prefix_map.get(tier_name, tier_name[:3])

def build_age_tier_abbrev_map(age_rules):
    """
    Build mapping from full AGE_TIER labels to compact display labels.

    Example output:
        "Benjamim (2018–2019)" → "B18/19"

    :param age_rules: AGE_RULES configuration from Config.
    :type age_rules: dict

    :return: Dictionary mapping full labels to abbreviations.
    :rtype: dict[str, str]
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
                year_part = ""
            else:
                year_part = "/".join(year_parts)

            abbrev_map[label] = f"{prefix}{year_part}"

    return abbrev_map

def abbreviate_age_tier(age_tier):
    """
    Convert full AGE_TIER string into compact tournament display format.

    Falls back to original label if no mapping exists.

    :param age_tier: Full age tier label.
    :type age_tier: str

    :return: Abbreviated age tier label.
    :rtype: str
    """
    if not age_tier:
        return ""

    normalized = str(age_tier).replace("-", "–").strip()
    return build_age_tier_abbrev_map(Config.AGE_RULES).get(normalized, normalized)


# =====================================================
# VALIDATION
# =====================================================

def validate_no_ungrouped(grouped_data, sex_label):
    """
    Validate that no athletes remain ungrouped in the dataset.

    This is a strict validation step:
    - If any ungrouped athletes exist, execution is halted
    - Full error report is generated for debugging

    :param grouped_data: Grouped YAML structure.
    :type grouped_data: dict

    :param sex_label: Gender label ("Male" / "Female").
    :type sex_label: str

    :raises ValueError: If ungrouped athletes are detected.
    :return: None
    :rtype: None
    """
    issues = []

    for age_tier, weight_classes in grouped_data.items():
        if not isinstance(weight_classes, dict):
            continue

        for weight_class, groups_dict in weight_classes.items():
            if not isinstance(groups_dict, dict):
                continue

            if "Ungrouped" in groups_dict:
                athletes = groups_dict["Ungrouped"]

                if isinstance(athletes, list) and athletes:
                    for athlete in athletes:
                        issues.append(
                            f'{sex_label} | {age_tier} | {weight_class} -> '
                            f'{athlete.get("Name", "Unknown")} '
                            f'({athlete.get("Club", "Unknown Club")}, '
                            f'{athlete.get("Weight", "?")}kg)'
                        )

    if issues:
        error_msg = "\n".join([
            "❌ Ungrouped athletes detected. Fix the YAML before mat distribution:\n",
            *[f"- {line}" for line in issues]
        ])
        raise ValueError(error_msg)
     

# =====================================================
# MAIN
# =====================================================

def run_mat_distribution(stage, number_of_mats):
    """
    Execute full mat distribution pipeline.

    Steps:
    1. Load grouped YAML files (male + female)
    2. Validate no ungrouped athletes exist
    3. Extract competition groups
    4. Merge all groups
    5. Distribute groups across mats
    6. Export YAML + PDF outputs

    :param stage: Tournament stage ("B" or "I").
    :type stage: str

    :param number_of_mats: Number of available mats.
    :type number_of_mats: int

    :return: Final mat distribution structure.
    :rtype: list[dict]
    """
    male_data = load_grouped_yaml(Config.male_grouped_file())
    female_data = load_grouped_yaml(Config.female_grouped_file())

    #Validate that there are no ungrouped athletes before proceeding
    validate_no_ungrouped(male_data, Config.MALE)
    validate_no_ungrouped(female_data, Config.FEMALE)

    male_groups = extract_groups_from_yaml(male_data, Config.MALE)
    female_groups = extract_groups_from_yaml(female_data, Config.FEMALE)

    all_groups = male_groups + female_groups

    if not all_groups:
        print(f"No valid groups found for stage {stage}.")
        return []

    mats = distribute_groups_to_mats(all_groups, number_of_mats)

    export_mat_distribution_yaml(mats, stage, Config.mat_distribution_yaml())
    export_mat_distribution_pdf(mats, Config.mat_distribution_pdf())

    return mats


if __name__ == "__main__":
    run_mat_distribution(Config.STAGE, Config.NUMBER_OF_MATS)