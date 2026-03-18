# Plot the output of simulate
import matplotlib.pyplot as plt


def plot(M, model_id, node_to_plot, perturbed_node, pert_duration, duration, full_trajectory, n_time_steps, pert_start_time=0):

  line, = plt.plot(range(0, pert_start_time+n_time_steps+1), full_trajectory[:, node_to_plot], marker='None', markersize=10, linewidth=2.5, label=f"Simulated", alpha=1.0)
  
  plt.title(f"Model {model_id}, {M.species_names[node_to_plot]} with forced {M.species_names[perturbed_node]} until t={duration}", fontsize=12)
  plt.xlabel("Time Steps")
  plt.xticks(range(0, len(full_trajectory)+1,20)) 
  plt.ylabel("State Level")
  plt.yticks([0, 1, 2])

  plt.xlim(-0.6, (n_time_steps+1)+0.8)
  plt.ylim(-0.1, 2.1)

  plt.savefig(f"./model{model_id}_state{node_to_plot}_{pert_duration}{perturbed_node}.png", dpi=300)
