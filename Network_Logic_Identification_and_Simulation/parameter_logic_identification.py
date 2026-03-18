# Parameter estimation as a CSP using lists as input

# import CPMpy libary 
import cpmpy as cp
import numpy as np
import pandas as pd
import math

# Read Excel file problem definition into dataframe
file="./MTb_Network-Chen_et_al_2026.xlsx"

# Path to output file
output_file="./models_out.csv"

# Solution limit
sol_limit=100

# Overall deviation at each constraint as percent of max departure  
perc_err=0.05

# Set with (1) or without (0) edge thresholds
edge_threshold_flag=1   # 1 is true, 0 is false

# Read relations 
known_relations = pd.read_excel(file,sheet_name="Relations",header=0,index_col=None,usecols="A:E",engine='openpyxl')
known_relations.info()

num_relations=len(known_relations.index)
known_polarity=np.array(known_relations.polarity, dtype='int')
known_certainty=np.array(known_relations.certainty, dtype='int')

# Read SS constraints
constr_state = pd.read_excel(file,sheet_name="SS_Constraints",header=0,index_col=None,engine='openpyxl')
constr_state.info()
num_state_var=len(constr_state.node)

# Extract constraints as state vectors  
num_constr=len(constr_state.columns[2:])  # recall constraints listed from 3rd column onwards
C_SS = np.array(constr_state[constr_state.columns[2:(2+num_constr)]],dtype='int')

# Initialize source and target variable index vectors
source_state_var_indices=np.ones((num_relations,1),dtype='int')*-99
target_state_var_indices=np.ones((num_relations,1),dtype='int')*-99

# Set range on free decision variables w and b - NOTE: still thinking about range on weights...
max_state=2
max_w = max_state # could be num_relations  

# This function will be called to associate weight and polarity - if one is zero the other must be zero and vice versa
def zero_dependency(w, p):
    return [
        (w == 0).implies(p == 0),
        (p == 0).implies(w == 0) 
    ]

# Setting tolerances in deviation from constraints

# Sum bits limit deviation at EACH constraint summed across all state variables                    
overall_bits_tol = int(perc_err*num_state_var*(max_state))       

# Enforces strict steady state adherence (next state = current state) within tolerance for EACH individual variable at each constraint
if overall_bits_tol==0:
    tol_ind_state_limit=0     
else:
    tol_ind_state_limit=max_state  # NOTE: could also be set by user

# Jury rigging sum deviations by alowing individual states at each constraint to deviate by no more than tol_ind_state_limit
tol_ind_state=cp.intvar(0, tol_ind_state_limit, shape=(num_state_var, num_constr), name="tol_ind_state")

# Allowing for unmeasured states as -99
state=cp.intvar(0, max_state, shape=(num_state_var, num_constr), name="state")

# Allowing for unknown polarities as -99
polarity=cp.intvar(-1, 1, shape=num_relations, name="polarity")

# Define free decision variables specific to each relation to support simple linear state transition  
w = cp.intvar(0, max_w, shape=num_relations, name="w")
# Careful: if Certainty is 1 for a relation then it cannot have a zero w; see code below

# Applying thresholds on upstream input signals in range 1 to max_state
if edge_threshold_flag==1:
    # define thresholds as a free variable
    thresholds=cp.intvar(1, max_state, shape=num_relations, name="thresholds")

# Assign state variable ID numbers to relations source and target variable names
for k in range(0,num_state_var):
    # find state var k name with state var index
    for r in range(0,num_relations):
        if known_relations.source[r]==constr_state.node[k]:
            source_state_var_indices[r]=k
        if known_relations.target[r]==constr_state.node[k]:
            target_state_var_indices[r]=k


# Looping through node state by appending each vector state transition constraint
m=cp.Model()

 #  Set up equality constraints for state  = measured value when measured (i.e. not -99)
for c in range(0,num_constr):
    for k in range(0,num_state_var):
        if C_SS[k,c] !=-99: # then measured
            m += state[k,c]==C_SS[k,c]

# Set up equality constraints for relations  = known value when specified (i.e. not -99)
for i in range (0,num_relations):
    if known_polarity[i] != -99 and known_certainty[i] ==1:
          # if polarity is known and edge presence is certain then use specified polarity
          m += polarity[i]==known_polarity[i]
          # weight w cannot be zero if edge presence is certain
          m += w[i]!=0    

    elif known_polarity[i]== -99 and known_certainty[i]==1:
          # if polarity is unknown and edge presence is certain then polarity is free non-zero variable 
          # polarity is free but must be non-zero
          m += polarity[i]!=0 # must be -1 or +1
          # weight w cannot be zero if edge presence is certain
          m += w[i]!=0        

    elif known_polarity[i] != -99 and known_certainty[i] !=1:
        # polarity is specified by LLM but edge presence is postulated and uncertain
        # use specified polarity 
        # m += polarity[i]==known_polarity[i]
        # if the edge weigth is not zero then use the specified polarity only
        m += (w[i] != 0).implies(polarity[i] == known_polarity[i])
        m += (w[i] == 0).implies(polarity[i] == 0)
        # allow edge weight to be zero - this will not inflate number of models as polarity is fixed

    else: 
        # polarity is unknown and edge presence is uncertain then both weights and polarities are free
        # but enforce zero weight means zero polarity and vice versa to avoid inflation of solution space
        m += zero_dependency(w[i], polarity[i])  


# Compute state transition for each steady state constraint c
# NOTE: removed bias term b[k]; setting b[k]=0 implcitly captures self-decay wo added relations

for c in range(0,num_constr):

    # Set up constraints for state transition at each state variable
    for k in range(0,num_state_var):
        # collect upstream input nodes for node k
        inp_relations_indices_k=np.where(target_state_var_indices==k)[0]
        inp_state_var_indices_k=source_state_var_indices[inp_relations_indices_k]

        if edge_threshold_flag==1:
            # Include simple threshold function Si/Tji suhc that S^i=0 if Si <= Tji
            m += (abs(cp.sum(state[inp_state_var_indices_k,c]//thresholds[inp_relations_indices_k]*w[inp_relations_indices_k]*polarity[inp_relations_indices_k]) - state[k,c]) ==  tol_ind_state[k,c])
        else:
            # Basic Lyman's piecewise linear with scaling and floor division wo thresholding
            m += (abs(cp.sum(state[inp_state_var_indices_k,c]*w[inp_relations_indices_k]*polarity[inp_relations_indices_k]) - state[k,c]) ==  tol_ind_state[k,c])

        # Avoid creating source nodes in solutions; sum of weights incoming must be > 0
        m += cp.sum(w[inp_relations_indices_k]) != 0

        # Controlling for only down regulation from upstream nodes; 
        # Need at least one upstream activator or node will go to floor value and remain
        m += cp.expressions.globalfunctions.Count(polarity[inp_relations_indices_k],1) != 0
        
        # Controlling for only upregulation regulation from upstream nodes
        # Need at least one upstream inactivator (or self decay) or node will go to ceiling value and remain
        # Caution: self-decay is implicit when state transition bias term b[k] = 0
        # m += cp.expressions.globalfunctions.Count(polarity[inp_relations_indices_k],-1) != 0

        # Avoid creating sink nodes in solutions; sum of weights outgoing must be > 0
        out_relations_indices_k=np.where(source_state_var_indices==k)[0]
        m += cp.sum(w[out_relations_indices_k]) != 0
    
    # Force sum deviaiton across all free variables at EACH constraint to be less than overall_bits_tol
    # (recall tol_ind_state_limit is applied implcitly in defining the range of tol_ind_state - no need to specifcy again)
    if tol_ind_state_limit != 0: 
        m += (cp.sum(tol_ind_state[0:num_state_var,c])<= overall_bits_tol)
    

# Attempting to store solutions
solutions = []
# Note: state.value() and tol_ind_state.value() are flattened in column-major order
# i.e. first k elements are state[0:k,0] of column of C1
if edge_threshold_flag==1:
    def collect(): 
            print(" w vector, polarity vector, thresholds vector, predicted state vector:",w.value(),polarity.value(),thresholds.value(),state.value(),tol_ind_state.value())
            solutions.append([list(w.value()),list(polarity.value()),list(thresholds.value()),list(state.value().flatten(order='F')),list(tol_ind_state.value().flatten(order='F'))])
else:
    def collect(): 
            print(" w vector, polarity vector, predicted state vector:",w.value(),polarity.value(),state.value(),tol_ind_state.value())
            solutions.append([list(w.value()),list(polarity.value()),list(state.value().flatten(order='F')),list(tol_ind_state.value().flatten(order='F'))])


# solve for all possible solutions 
n = m.solveAll(display=collect,solution_limit=sol_limit) # set max number of solutions

print("Status:", m.status())  
if n:
   print(f"Stored {len(solutions)} solutions.") # Nr of solutions
   if edge_threshold_flag==1:
        df_solutions = pd.DataFrame(solutions,columns=["relations weight w","relations polarity","relations thresholds","predicted state","deviations"])
   else:
        df_solutions = pd.DataFrame(solutions,columns=["relations weight w","relations polarity","predicted state","deviations"])
   
   # write to csv output file
   df_solutions.to_csv(output_file)

else:
    print("No solution found.")
    from cpmpy.tools import mus
    print(mus(m.constraints))