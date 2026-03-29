from config import Config
import os
import random
import yaml
import pandas as pd
import pandas as pd
import os
import yaml
import random

# =========================================================
# CONFIG
# =========================================================

DF_ALL = pd.read_excel(f'Input/judo+_{Config.TOURNAMENT_CODE}.xlsx', sheet_name=Config.STAGE, header=None).drop([0])
    
os.makedirs(Config.output_folder(), exist_ok=True)

# =========================================================
# HELPERS: EXPORT
# =========================================================

def export_markdown_report(results):
    """
    Export one unified Markdown report containing:
    - metadata
    - male details
    - female details
    - logs / warnings
    - summaries
    """
    if Config.STAGE == "B":
        output_md_file = os.path.join(Config.output_folder(), f"{Config.STAGE}_draw_report.md")
    elif Config.STAGE == "I":
        output_md_file = os.path.join(Config.output_folder(), f"{Config.STAGE}_draw_report.md")

    lines = []

    # =====================================================
    # HEADER / METADATA
    # =====================================================
    lines.append(f"# Tournament Draw Report")
    lines.append("")
    lines.append(f"- **Tournament Code:** `{Config.TOURNAMENT_CODE}`")
    lines.append(f"- **Stage:** `{Config.STAGE}`")
    lines.append(f"- **Random Seed:** `{Config.RANDOM_SEED}`")
    lines.append(f"- **Input File:** `Input/judo+_{Config.TOURNAMENT_CODE}.xlsx`")
    lines.append("")

    male_summary = results["Male"]["summary"]
    female_summary = results["Female"]["summary"]

    overall_input = male_summary["Total Athletes Input"] + female_summary["Total Athletes Input"]
    overall_grouped = male_summary["Total Athletes Grouped"] + female_summary["Total Athletes Grouped"]
    overall_ungrouped = male_summary["Total Athletes Ungrouped"] + female_summary["Total Athletes Ungrouped"]
    overall_accounted = male_summary["Total Athletes Accounted For"] + female_summary["Total Athletes Accounted For"]
    overall_check = (overall_input == overall_accounted)

    lines.append("## Overall Summary")
    lines.append("")
    lines.append(f"- **Total Athletes Input:** {overall_input}")
    lines.append(f"- **Total Athletes Grouped:** {overall_grouped}")
    lines.append(f"- **Total Athletes Ungrouped:** {overall_ungrouped}")
    lines.append(f"- **Total Athletes Accounted For:** {overall_accounted}")
    lines.append(f"- **Overall Check Passed:** {'Yes' if overall_check else 'No'}")
    lines.append("")

    # =====================================================
    # PER-GENDER SECTION
    # =====================================================
    for sex_label in [Config.MALE, Config.FEMALE]:
        summary = results[sex_label]["summary"]
        logs = results[sex_label]["logs"]

        lines.append("---")
        lines.append("")
        lines.append(f"# {sex_label}")
        lines.append("")

        # ---------------------------------------------
        # SUMMARY
        # ---------------------------------------------
        lines.append("## Summary")
        lines.append("")
        lines.append(f"- **Total Athletes Input:** {summary['Total Athletes Input']}")
        lines.append(f"- **Total Athletes Grouped:** {summary['Total Athletes Grouped']}")
        lines.append(f"- **Total Athletes Ungrouped:** {summary['Total Athletes Ungrouped']}")
        lines.append(f"- **Total Athletes Accounted For:** {summary['Total Athletes Accounted For']}")
        lines.append(f"- **Check Passed:** {'Yes' if summary['Check Passed'] else 'No'}")
        lines.append("")

        # ---------------------------------------------
        # SUMMARY BY AGE TIER / WEIGHT CLASS
        # ---------------------------------------------
        lines.append("## Breakdown by Age Tier / Weight Class")
        lines.append("")

        if not summary["Age Tiers"]:
            lines.append("_No summary data available._")
            lines.append("")
        else:
            for age_tier, age_info in summary["Age Tiers"].items():
                lines.append(f"### {age_tier}")
                lines.append("")
                lines.append(f"- **Athletes in Age Tier:** {age_info['Athletes']}")
                lines.append("")

                for weight_class, wc_info in age_info["Weight Classes"].items():
                    lines.append(f"- **{weight_class}**")
                    lines.append(f"  - Athletes: {wc_info['Athletes']}")
                    lines.append(f"  - Groups: {wc_info['Groups']}")
                    lines.append(f"  - Grouped Athletes: {wc_info['Grouped Athletes']}")
                    lines.append(f"  - Ungrouped Athletes: {wc_info['Ungrouped Athletes']}")

                lines.append("")

        # ---------------------------------------------
        # LOGS / WARNINGS
        # ---------------------------------------------
        lines.append("## Logs / Warnings")
        lines.append("")

        if not logs:
            lines.append("_No warnings or validation issues._")
            lines.append("")
        else:
            for log_line in logs:
                lines.append(f"- {log_line}")
            lines.append("")

    # =====================================================
    # WRITE FILE
    # =====================================================
    with open(output_md_file, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"Markdown report saved to {output_md_file}")


def export_groups_to_yaml(grouped_data, sex_label="Unknown"):
    """
    Export grouped athletes / ungrouped athletes to a YAML file.
    """
    if Config.STAGE == "B":
        output_yaml_file = os.path.join(Config.output_folder(), f"{Config.STAGE}_{sex_label}_grouped_athletes.yaml")
    elif Config.STAGE == "I":
        output_yaml_file = os.path.join(Config.output_folder(), f"{Config.STAGE}_{sex_label}_grouped_athletes.yaml")

    with open(output_yaml_file, "w", encoding="utf-8") as f:
        yaml.safe_dump(
            grouped_data,
            f,
            allow_unicode=True,
            sort_keys=False,
            default_flow_style=False
        )

    print(f"Grouped athletes for {sex_label} saved to {output_yaml_file}")

# =========================================================
# HELPERS: VALIDATION / NORMALIZATION
# =========================================================

def normalize_gender(value):
    if pd.isna(value):
        return None
    g = str(value).strip().upper()
    if g in ["M", "MALE", "MASCULINO", "MASC"]:
        return "M"
    if g in ["F", "FEMALE", "FEMININO", "FEM"]:
        return "F"
    return None


def normalize_tier(value):
    """
    Normalize plural/singular and casing.
    """
    if pd.isna(value):
        return None

    tier = str(value).strip().lower()

    tier_map = {
        "benjamim": "Benjamim",
        "benjamins": "Benjamim",
        "infantil": "Infantil",
        "infantis": "Infantil",
        "iniciado": "Iniciado",
        "iniciados": "Iniciado"
    }

    return tier_map.get(tier, None)


def create_subgroup(row, logs):
    """
    Create AGE_TIER from TIER + BIRTH_YEAR using configurable AGE_RULES.
    Returns None if invalid, and logs the reason.
    """
    athlete_name = str(row["NAME"]).strip()

    tier = normalize_tier(row["TIER"])
    if tier is None:
        logs.append(f'Athlete "{athlete_name}" has an invalid TIER: {row["TIER"]}')
        return None

    birth_year = pd.to_numeric(pd.Series([row["BIRTH_YEAR"]]), errors="coerce").iloc[0]
    if pd.isna(birth_year):
        logs.append(f'Athlete "{athlete_name}" has an invalid BIRTH_YEAR: {row["BIRTH_YEAR"]}')
        return None

    birth_year = int(birth_year)

    # Validate tier exists in rules
    if tier not in Config.AGE_RULES:
        logs.append(f'Athlete "{athlete_name}" has no configured AGE_RULES for TIER: {tier}')
        return None

    # Find matching subgroup rule
    for subgroup_rule in Config.AGE_RULES[tier]:
        if birth_year in subgroup_rule["years"]:
            return subgroup_rule["label"]

    # No match found
    allowed_years = sorted({
        year
        for subgroup_rule in Config.AGE_RULES[tier]
        for year in subgroup_rule["years"]
    })

    logs.append(
        f'Athlete "{athlete_name}" has unsupported {tier} BIRTH_YEAR: {birth_year}. '
        f'Allowed years for {tier}: {allowed_years}'
    )
    return None


# =========================================================
# STEP 1: PREPARE TABLE
# =========================================================

def process_table(df):
    """
    Process the raw table:
    - set column names
    - normalize gender
    - create AGE_TIER with validation logs
    - keep invalid rows out of main draw
    - return male/female dataframes + logs
    """

    logs = []

    # Adjust if your source columns come in a known order
    df = df.copy()
    df.columns = ['NAME', 'GENDER', 'TIER', 'BIRTH_YEAR', 'WEIGHT', 'CLUB']

    # Normalizations
    df["NAME"] = df["NAME"].astype(str).str.strip()
    df["GENDER"] = df["GENDER"].apply(normalize_gender)
    df["CLUB"] = df["CLUB"].astype(str).str.strip().str.upper()

    invalid_gender_mask = df["GENDER"].isna()
    if invalid_gender_mask.any():
        for _, row in df[invalid_gender_mask].iterrows():
            logs.append(f'Athlete "{row["NAME"]}" has an invalid GENDER: {row["GENDER"]}')
        df = df[~invalid_gender_mask].copy()

    # Create AGE_TIER
    df["AGE_TIER"] = df.apply(lambda row: create_subgroup(row, logs), axis=1)

    # Keep only valid rows for the draw
    invalid_age_tier_mask = df["AGE_TIER"].isna()
    invalid_rows = df[invalid_age_tier_mask].copy()
    valid_df = df[~invalid_age_tier_mask].copy()

    if not invalid_rows.empty:
        logs.append(f"{len(invalid_rows)} athletes were excluded before grouping due to invalid AGE_TIER.")

    # Split by gender
    df_m = valid_df[valid_df["GENDER"] == "M"].copy()
    df_f = valid_df[valid_df["GENDER"] == "F"].copy()

    # Drop GENDER after split
    df_m = df_m.drop(columns=["GENDER"])
    df_f = df_f.drop(columns=["GENDER"])

    return df_m, df_f, logs


# =========================================================
# STEP 2: ASSIGN WEIGHT CLASSES
# =========================================================

def assign_weight_class(df, bins, labels, logs):
    """
    Convert WEIGHT to numeric and assign WEIGHT_CLASS.
    Invalid weights are logged and removed.
    """
    df = df.copy()

    # Keep original for logging
    df["WEIGHT_RAW"] = df["WEIGHT"]

    # Normalize weight strings
    df["WEIGHT"] = (
        df["WEIGHT"]
        .astype(str)
        .str.replace(",", ".", regex=False)
        .str.strip()
    )

    df["WEIGHT"] = pd.to_numeric(df["WEIGHT"], errors="coerce")

    invalid_weight_mask = df["WEIGHT"].isna()
    if invalid_weight_mask.any():
        for _, row in df[invalid_weight_mask].iterrows():
            logs.append(
                f'Athlete "{row["NAME"]}" has an invalid WEIGHT: {row["WEIGHT_RAW"]}'
            )

    # Remove invalid weights
    df = df[~invalid_weight_mask].copy()

    # Assign official fixed class
    df["WEIGHT_CLASS"] = pd.cut(
        df["WEIGHT"],
        bins=bins,
        labels=labels,
        right=True,
        include_lowest=True
    )

    # Just in case
    invalid_wc_mask = df["WEIGHT_CLASS"].isna()
    if invalid_wc_mask.any():
        for _, row in df[invalid_wc_mask].iterrows():
            logs.append(
                f'Athlete "{row["NAME"]}" could not be assigned a WEIGHT_CLASS for WEIGHT={row["WEIGHT"]}'
            )
        df = df[~invalid_wc_mask].copy()

    # Remove temp column
    df = df.drop(columns=["WEIGHT_RAW"])

    # Sort for consistency
    df = df[['NAME', 'TIER', 'BIRTH_YEAR', 'AGE_TIER', 'WEIGHT', 'WEIGHT_CLASS', 'CLUB']].sort_values(
        by=['AGE_TIER', 'WEIGHT_CLASS', 'WEIGHT'],
        ascending=[True, True, True]
    ).reset_index(drop=True)

    return df


# =========================================================
# STEP 3: GROUP SIZE STRATEGY
# =========================================================

def choose_group_sizes(n):
    """
    Choose group sizes from {2,3,4,5}, preferring 3 and 4.
    Can leave 1 athlete ungrouped if needed.
    Returns (group_sizes, leftover)
    """
    # We prefer:
    # - no leftover if possible
    # - 3 and 4 preferred
    # - 2 and 5 allowed
    # - leftover 1 is acceptable

    candidates = []

    # Brute force small combinations (safe for this use case)
    max_groups = max(1, n // 2 + 2)

    for a in range(max_groups):  # count of 2s
        for b in range(max_groups):  # count of 3s
            for c in range(max_groups):  # count of 4s
                for d in range(max_groups):  # count of 5s
                    total = 2*a + 3*b + 4*c + 5*d
                    if total > n:
                        continue

                    leftover = n - total
                    if leftover not in [0, 1]:
                        continue

                    group_sizes = [2]*a + [3]*b + [4]*c + [5]*d
                    if not group_sizes:
                        continue

                    # Scoring:
                    # 1) prefer no leftover
                    # 2) prefer more 3s and 4s
                    # 3) penalize 2s and 5s a bit
                    # 4) prefer fewer groups slightly
                    score = 0
                    score += 1000 if leftover == 0 else 0
                    score += 20 * b  # 3s
                    score += 20 * c  # 4s
                    score -= 5 * a   # 2s
                    score -= 5 * d   # 5s
                    score -= len(group_sizes)

                    candidates.append((score, group_sizes, leftover))

    if not candidates:
        # Special cases: n = 1
        return [], n

    # Best candidate
    candidates.sort(key=lambda x: x[0], reverse=True)
    best_group_sizes = candidates[0][1]
    leftover = candidates[0][2]

    # Nice presentation: larger groups first or 3/4 first
    best_group_sizes.sort(reverse=True)

    return best_group_sizes, leftover


# =========================================================
# STEP 4: CLUB-AWARE GROUP BUILDING
# =========================================================

def athlete_to_yaml_dict(row):
    """
    Convert one athlete row to YAML-friendly dict.
    """
    return {
        "Name": row["NAME"],
        "Weight": float(row["WEIGHT"]),
        "Club": row["CLUB"],
        "Birth Year": int(row["BIRTH_YEAR"])
    }


def order_group_same_club_first(group_df, logs=None, age_tier=None, weight_class=None):
    """
    Reorder athletes inside a group so that athletes from duplicated clubs
    appear first, grouped together.

    Also optionally logs unavoidable same-club pairings.
    """
    group_df = group_df.copy().reset_index(drop=True)

    club_counts = group_df["CLUB"].value_counts()
    duplicated_clubs = club_counts[club_counts > 1]

    if logs is not None and not duplicated_clubs.empty:
        for club, count in duplicated_clubs.items():
            logs.append(
                f'Same-club pairing in {age_tier} / {weight_class}: '
                f'club "{club}" appears {count} times in one group.'
            )

    duplicated_clubs_set = set(duplicated_clubs.index)

    duplicated_df = group_df[group_df["CLUB"].isin(duplicated_clubs_set)].copy()
    unique_df = group_df[~group_df["CLUB"].isin(duplicated_clubs_set)].copy()

    duplicated_df = duplicated_df.sort_values(
        by=["CLUB", "WEIGHT"],
        ascending=[True, True]
    )

    unique_df = unique_df.sort_values(
        by=["WEIGHT", "CLUB"],
        ascending=[True, True]
    )

    ordered_df = pd.concat([duplicated_df, unique_df], ignore_index=True)

    return ordered_df


def pick_group_with_club_mix(pool_df, group_size):
    """
    Build one group trying to maximize club diversity.
    Randomized among valid candidates while remaining reproducible.
    """
    if len(pool_df) < group_size:
        return pd.DataFrame(), pool_df

    # Reproducible shuffle controlled by RANDOM_SEED
    shuffle_seed = Config.rng().randint(0, 10**9)
    pool_df = pool_df.sample(frac=1, random_state=shuffle_seed).reset_index(drop=True)

    selected_indices = []

    # Start with a random athlete from the shuffled pool
    selected_indices.append(0)
    used_clubs = {pool_df.loc[0, "CLUB"]}

    while len(selected_indices) < group_size:
        available_indices = [idx for idx in range(len(pool_df)) if idx not in selected_indices]

        # Prefer athletes from clubs not yet used in the group
        new_club_candidates = [
            idx for idx in available_indices
            if pool_df.loc[idx, "CLUB"] not in used_clubs
        ]

        # Random choice among valid candidates
        if new_club_candidates:
            found = Config.rng().choice(new_club_candidates)
        else:
            found = Config.rng().choice(available_indices)

        selected_indices.append(found)
        used_clubs.add(pool_df.loc[found, "CLUB"])

    group_df = pool_df.loc[selected_indices].copy()
    remaining_df = pool_df.drop(index=selected_indices).reset_index(drop=True)

    return group_df, remaining_df


def build_groups_for_class(class_df, logs, age_tier, weight_class):
    """
    Build groups for one AGE_TIER + WEIGHT_CLASS subset.
    Returns:
    {
        "Group1": [...],
        "Group2": [...],
        "Ungrouped": [...]
    }
    """
    n = len(class_df)
    result = {}

    if n == 0:
        return result

    group_sizes, leftover = choose_group_sizes(n)

    # If only 1 athlete total
    if not group_sizes and n == 1:
        athlete = athlete_to_yaml_dict(class_df.iloc[0])
        result["Ungrouped"] = [athlete]
        logs.append(
            f'1 lone athlete in {age_tier} / {weight_class}: "{class_df.iloc[0]["NAME"]}" left ungrouped.'
        )
        return result

    pool_df = class_df.copy().reset_index(drop=True)

    # Build groups
    groups_list = []

    for group_size in group_sizes:
        group_df, pool_df = pick_group_with_club_mix(pool_df, group_size)

        # If unavoidable same-club athletes exist, place them first in the group
        group_df = order_group_same_club_first(
            group_df,
            logs=logs,
            age_tier=age_tier,
            weight_class=weight_class
        )

        groups_list.append([athlete_to_yaml_dict(row) for _, row in group_df.iterrows()])

    # Shuffle group order for more visible randomness
    Config.rng().shuffle(groups_list)

    for i, group in enumerate(groups_list, start=1):
        result[f"Group{i}"] = group

    # Leftover (0 or 1)
    if leftover > 0 and not pool_df.empty:
        ungrouped = [athlete_to_yaml_dict(row) for _, row in pool_df.iterrows()]
        result["Ungrouped"] = ungrouped

        for _, row in pool_df.iterrows():
            logs.append(
                f'Lone athlete in {age_tier} / {weight_class}: "{row["NAME"]}" left ungrouped pending manual review.'
            )

    return result


# =========================================================
# STEP 5: BUILD FULL GROUPED STRUCTURE
# =========================================================

def build_grouped_structure(df, logs, sex_label="Unknown"):
    grouped_output = {}

    if df.empty:
        logs.append(f"No valid athletes available for {sex_label}.")
        return grouped_output

    for age_tier in sorted(df["AGE_TIER"].dropna().unique()):
        age_df = df[df["AGE_TIER"] == age_tier].copy()
        grouped_output[age_tier] = {}

        present_classes = set(age_df["WEIGHT_CLASS"].dropna())

        for weight_class in age_df["WEIGHT_CLASS"].cat.categories:
            if weight_class not in present_classes:
                continue

            wc_df = (
                age_df[age_df["WEIGHT_CLASS"] == weight_class]
                .copy()
                .sort_values(by="WEIGHT")
            )

            class_result = build_groups_for_class(
                wc_df,
                logs=logs,
                age_tier=age_tier,
                weight_class=str(weight_class)
            )

            grouped_output[age_tier][str(weight_class)] = class_result

    return grouped_output


# =========================================================
# STEP 6: BUILD SUMMARY
# =========================================================

def build_summary_from_grouped(grouped_data, sex_label="Unknown"):
    """
    Build a separate summary structure from grouped YAML data.
    """
    total_grouped = 0
    total_ungrouped = 0

    summary = {
        "Gender": sex_label,
        "Random Seed": Config.RANDOM_SEED,
        "Total Athletes Input": 0,
        "Total Athletes Grouped": 0,
        "Total Athletes Ungrouped": 0,
        "Total Athletes Accounted For": 0,
        "Check Passed": False,
        "Age Tiers": {}
    }

    for age_tier, weight_classes in grouped_data.items():
        age_tier_total = 0
        age_tier_summary = {
            "Athletes": 0,
            "Weight Classes": {}
        }

        for weight_class, groups_dict in weight_classes.items():
            wc_total = 0
            wc_grouped = 0
            wc_ungrouped = 0
            wc_group_count = 0

            for key, athlete_list in groups_dict.items():
                if key == "Ungrouped":
                    wc_ungrouped += len(athlete_list)
                    wc_total += len(athlete_list)
                elif key.startswith("Group"):
                    wc_group_count += 1
                    wc_grouped += len(athlete_list)
                    wc_total += len(athlete_list)

            age_tier_summary["Weight Classes"][weight_class] = {
                "Athletes": wc_total,
                "Groups": wc_group_count,
                "Grouped Athletes": wc_grouped,
                "Ungrouped Athletes": wc_ungrouped
            }

            age_tier_total += wc_total
            total_grouped += wc_grouped
            total_ungrouped += wc_ungrouped

        age_tier_summary["Athletes"] = age_tier_total
        summary["Age Tiers"][age_tier] = age_tier_summary
        summary["Total Athletes Input"] += age_tier_total

    summary["Total Athletes Grouped"] = total_grouped
    summary["Total Athletes Ungrouped"] = total_ungrouped
    summary["Total Athletes Accounted For"] = total_grouped + total_ungrouped
    summary["Check Passed"] = (
        summary["Total Athletes Input"] == summary["Total Athletes Accounted For"]
    )

    return summary


# =========================================================
# STEP 7: FULL PIPELINE FOR ONE GENDER
# =========================================================

def process_gender_pipeline(df_gender, bins, labels, sex_label, logs):
    """
    Full pipeline for one gender:
    - assign weight class
    - build groups
    - build summary
    - export files
    """
    # Assign weight classes
    df_gender = assign_weight_class(df_gender, bins, labels, logs)

    # Build grouped structure
    grouped_data = build_grouped_structure(df_gender, logs, sex_label=sex_label)

    # Build summary
    summary_data = build_summary_from_grouped(grouped_data, sex_label=sex_label)

    # Export
    export_groups_to_yaml(grouped_data, sex_label=sex_label)

    return grouped_data, summary_data


# =========================================================
# STEP 8: MASTER PIPELINE
# =========================================================

def run_tournament_draw(df_all):
    """
    Master function:
    1) process raw table
    2) split male/female
    3) run per-gender pipeline
    4) return outputs
    """
    # Process initial table
    df_m, df_f, global_logs = process_table(df_all)

    # Separate logs per gender (copy shared preprocessing logs to both, or keep separate if preferred)
    male_logs = []
    female_logs = []

    # Male pipeline
    male_grouped_data, male_summary = process_gender_pipeline(
        df_gender=df_m,
        bins=Config.MASC_BINS,
        labels=Config.MASC_LABELS,
        sex_label=Config.MALE,
        logs=male_logs
    )

    # Female pipeline
    female_grouped_data, female_summary = process_gender_pipeline(
        df_gender=df_f,
        bins=Config.FEM_BINS,
        labels=Config.FEM_LABELS,
        sex_label=Config.FEMALE,
        logs=female_logs
    )

    results = {
        "Global": {
            "logs": global_logs
        },
        "Male": {
            "summary": male_summary,
            "logs": male_logs
        },
        "Female": {
            "summary": female_summary,
            "logs": female_logs
        }
    }

    # Export one unified markdown report
    export_markdown_report(results)


# =========================================================
# USAGE
# =========================================================

if __name__ == "__main__":
    run_tournament_draw(DF_ALL)