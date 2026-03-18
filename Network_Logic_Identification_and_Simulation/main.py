from parse_models import read_model_data
from simulate import simulate
from plot import plot

############################################## ADJUSTABLE PARAMETERS ##############################################

model_num = 50 # Model index number (0-99)
perturbed_node = 0 # Index of node to be perturbed. See Mtb_network.xlsx ('SS_Constraints') for node indices.
perturbation_duration = 'pulse' # or 'continuous'
node_to_plot = 62 # cAMP = 62. Refer to Excel file for other species' indices.

##################################################################################################################


# Path to network xlsx file
sourceTarget_file = "./MTb_Network-Chen_et_al_2026.xlsx"

# Path to the model csv file
models_file="./models_out_example.csv"


# usually this is set to 2 (0 = low, 1 = baseline, 2 = high)
max_state = 2


# Number of time steps to take
n_time_steps = 100

# Perturbation params
pert_start_time = 0
level = 2

species_to_plot = [node_to_plot]


# Set to 0 or 1 depending on whether thresholds are being considered
thresholds_flag = 1

# Set update scheme
scheme = 'synchronous'

##########################################################################


if __name__ == "__main__":
  
  M = read_model_data(sourceTarget_file, models_file, max_state, thresholds_flag, model_num)
  print(f"Simulating Model {model_num} with {M.species_names[perturbed_node]} {perturbation_duration}, plotting {M.species_names[node_to_plot]} response.")
  
  
  if perturbation_duration == 'pulse':
    duration = n_time_steps//2
  elif perturbation_duration == 'continuous':
    duration = n_time_steps
  
  perturbed_species = {
      perturbed_node: (2, pert_start_time, duration)
  }
  

  full_traj = simulate(n_time_steps, M, perturbed_species=perturbed_species)
  plot(M, model_num, node_to_plot, perturbed_node, perturbation_duration, duration, full_traj, n_time_steps)
  
