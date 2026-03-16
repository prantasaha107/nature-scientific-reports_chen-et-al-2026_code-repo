import os
import numpy as np
import pandas as pd
from cleanlab_studio import Studio

# --- API key setup -----------------------------------------------------------
from CleanLabkey import TLM_key          # import key from local python file
os.environ['API_KEY'] = TLM_key

# --- CleanLab Studio client --------------------------------------------------
studio = Studio(TLM_key)

# --- Model type selection ----------------------------------------------------
# 1 = Single TLM model (response + trustworthiness in one call)
# 2 = Dual hybrid model (separate models for response and score)
# 3 = Trustworthiness score only (reuses responses from a prior run)
model_type = 1

if model_type == 1:
    tlm = studio.TLM(
        quality_preset="medium",
        options={"model": "gpt-4", "num_consistency_samples": 10}
    )
elif model_type == 2:
    model_for_response = studio.TLM(
        quality_preset="base",
        options={"model": "gpt-4"}
    )
    model_for_score = studio.TLM(
        quality_preset="medium",
        options={"num_consistency_samples": 10}   # defaults to gpt-3.5
    )
# model_type == 3 uses model_for_score, initialised inside the loop below

# --- Input file --------------------------------------------------------------
file = "embio-protein-entities_Mtb_API_test.xlsx"

# Read source and target entity lists (singl column each)
source_entities = pd.read_excel(
    file, sheet_name="source_entities",
    header=0, index_col=None, usecols="A", engine="openpyxl"
)
target_entities = pd.read_excel(
    file, sheet_name="target_entities",
    header=0, index_col=None, usecols="A", engine="openpyxl"
)

source_node = np.array(source_entities)   # shape: (n_sources, 1)
target_node  = np.array(target_entities)  # shape: (n_targets, 1)

# For model_type==3 load prior responses to re-score
if model_type == 3:
    query_results = pd.read_excel(
        file, sheet_name="query_results",
        header=0, index_col=None, usecols="A:C", engine="openpyxl"
    )
    model_for_score = studio.TLM(
        quality_preset="medium",
        options={"num_consistency_samples": 10}
    )

# --- Query repeat count ------------------------------------------------------
num_r = 1 if model_type != 3 else query_results.shape[1]

# --- Helper: run a single query string through the chosen model --------------
def run_query(query_str, prior_response=None):
    """
    Send one query to the TLM and return (response_str, trust_score_str).

    For model_type 3, prior_response must be supplied (str); the model only
    computes a trustworthiness score without generating a new response.
    """
    q = [query_str]   # TLM expects a list

    if model_type == 1:
        out = tlm.prompt(q)
        return str(out[0]["response"]), str(out[0]["trustworthiness_score"])

    elif model_type == 2:
        out = model_for_response.prompt(q)
        resp = str(out[0]["response"])
        score = model_for_score.get_trustworthiness_score(q, response=[resp])
        return resp, str(score)

    else:   # model_type == 3
        score = model_for_score.get_trustworthiness_score(
            q, response=[prior_response]
        )
        return str(prior_response), str(score)


# --- Build column header list ------------------------------------------------
# For each repeat we add four columns: Q1 response, Q1 trust, Q2 response, Q2 trust
def repeat_headers(r_index):
    n = r_index + 1
    return [
        f"Relation Polarity {n}", f"Trustworthiness {n}",          # Q1 (original names)
        f"Q2 Relation Polarity {n}", f"Q2 Trustworthiness {n}",    # Q2 (new)
    ]

# --- Main query loop ---------------------------------------------------------
table_out = None

for r in range(num_r):
    print(f"\n=== Repeat {r + 1} of {num_r} ===")
    repeat_rows = []   # collect one row per valid (source, target) pair

    i = 0   # flat index used to look up prior responses for model_type==3
    for t in range(len(target_node)):
        for s in range(len(source_node)):

            # Skip self-loops
            if target_node[t, 0] == source_node[s, 0]:
                continue

            src_name = source_entities.iloc[s, 0]
            tgt_name = target_entities.iloc[t, 0]

            # ------------------------------------------------------------------
            # Q1: Does protein [source] regulate messenger molecule [target]?
            # ------------------------------------------------------------------
            q1 = (
                f"Does protein {src_name} regulate messenger molecule {tgt_name}"
                " (1) positively, (2) negatively or (3) not at all?"
                " Respond with only one choice"
            )

            # ------------------------------------------------------------------
            # Q2: Does messenger molecule [source] regulate protein [target]?
            # ------------------------------------------------------------------
            q2 = (
                f"Does messenger molecule {src_name} regulate protein {tgt_name}"
                " (1) positively, (2) negatively or (3) not at all?"
                " Respond with only one choice"
            )

            # Fetch prior responses when only re-scoring (model_type==3)
            prior_q1 = query_results.values[i, r] if model_type == 3 else None
            prior_q2 = None   # extend if you store Q2 results across runs

            # Run both queries
            print(f"  [{i}] {src_name} ↔ {tgt_name}")
            resp_q1, trust_q1 = run_query(q1, prior_q1)
            resp_q2, trust_q2 = run_query(q2, prior_q2)
            print(f"    Q1 → {resp_q1}  (trust: {trust_q1})")
            print(f"    Q2 → {resp_q2}  (trust: {trust_q2})")

            if r == 0:
                # First repeat: store source, target and both query results
                repeat_rows.append([
                    source_node[s, 0], target_node[t, 0],
                    resp_q1, trust_q1,
                    resp_q2, trust_q2,
                ])
            else:
                # Subsequent repeats: only the new scores (no source/target cols)
                repeat_rows.append([resp_q1, trust_q1, resp_q2, trust_q2])

            i += 1

    # Stack rows for this repeat into a 2-D array
    repeat_array = np.array(repeat_rows, dtype=object)

    if r == 0:
        table_out = repeat_array
    else:
        table_out = np.hstack((table_out, repeat_array))

# --- Assemble final DataFrame ------------------------------------------------
base_cols = ["Source", "Target"]
extra_cols = []
for r in range(num_r):
    extra_cols.extend(repeat_headers(r))

relation_table = pd.DataFrame(table_out, columns=base_cols + extra_cols)

# --- Save to CSV -------------------------------------------------------------
output_map = {
    1: "embio-protein-entities_Mtb_validation_single_model_TLM_API_test_relations.csv",
    2: "embio-protein-entities_Mtb_validation_hybrid_model_TLM_API_test_relations.csv",
    3: "embio-protein-entities_Mtb_Score_Only_TLM_API_test_relations.csv",
}
out_path = output_map[model_type]
relation_table.to_csv(out_path, index=False)
print(f"\nResults saved to: {out_path}")
print(relation_table.head())