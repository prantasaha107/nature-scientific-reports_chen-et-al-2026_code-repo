# =============================================================================
# Otsu Thresholding on TLM Trustworthiness Scores
# =============================================================================
# Reads trustworthiness scores and TLM responses from an Excel file,
# filters out "no interaction" responses (coded as -99), then applies
# Otsu's method to find the optimal threshold that splits scores into
# two groups (foreground / background) by minimising within-class variance.
# =============================================================================

import numpy as np
import pandas as pd

# --- Load data ---------------------------------------------------------------

# Columns C and D (0-indexed: 2 and 3) hold the TLM Response and
# Trustworthiness Score respectively
COLS = [2, 3]
FILE = "/Users/chris/Desktop/indra/tlm_responses.xlsx"

df = pd.read_excel(FILE, usecols=COLS)
print("Loaded columns:", df.axes)

# --- Filter out "no interaction" rows ----------------------------------------
# TLM responses coded as -99 indicate no interaction; exclude these from
# the threshold analysis

scores = []
for idx in range(len(df)):
    response = df.at[idx, "TLM Response"].item()
    if response != -99:
        scores.append(df.at[idx, "Trustworthiness Score"].item())

n_total    = len(df)
n_filtered = len(scores)
print(f"Initial number of responses:  {n_total}")
print(f"Final number of responses:    {n_filtered}")
print(f"Responses filtered out:       {n_total - n_filtered}")

# --- Prepare sorted unique scores --------------------------------------------
# Otsu's method iterates over unique candidate thresholds; descending order
# means we step from high scores to low scores as k increases.

unique_scores = sorted(np.unique(scores), reverse=True)
arr_scores    = np.array(unique_scores)
p             = len(unique_scores)

# --- Otsu's method -----------------------------------------------------------
# For each candidate threshold k we split the scores into:
#   foreground (fg): scores >= threshold  →  the "trustworthy" group
#   background (bg): scores <  threshold  →  the "untrustworthy" group
#
# We minimise the weighted within-class variance:
#   W_fg * Var(fg)  +  W_bg * Var(bg)
#
# bg_var_weight lets you up-weight the background term if the two groups
# are expected to be unequally sized or important.

bg_var_weight = 1  # set > 1 to penalise background non-uniformity more

least_variance           = -1   # sentinel: not yet set
least_variance_threshold = -1
k_least_variance         = -1

for k in range(1, p - 1):
    threshold = unique_scores[k]

    # Background: scores strictly below the threshold
    bg = arr_scores[arr_scores <  threshold]
    weight_bg   = len(bg) / p
    variance_bg = bg_var_weight * np.var(bg)

    # Foreground: scores at or above the threshold
    fg = arr_scores[arr_scores >= threshold]
    weight_fg   = len(fg) / p
    variance_fg = np.var(fg)

    within_class_variance = weight_fg * variance_fg + weight_bg * variance_bg

    # Keep track of the threshold that gives the lowest within-class variance
    if least_variance == -1 or within_class_variance < least_variance:
        least_variance           = within_class_variance
        least_variance_threshold = threshold
        k_least_variance         = k
        print(f"  New best — variance: {within_class_variance:.6f}  threshold: {threshold:.6f}")

# --- Results -----------------------------------------------------------------
print(f"\nOtsu threshold:      {least_variance_threshold}")
print(f"Corresponding index: {k_least_variance}")