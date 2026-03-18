# Update state variables based on model parameters and given perturbation with a synchronous update scheme
import numpy as np


# Helper function for allowing an increment > 1
def find_increment(max_increment, max_state, delta_S, current_state):
  #Case 1: Image is much higher than current and we want to increment as much as possible
  if (delta_S > 0) and (abs(delta_S) >= max_increment):
    if current_state <= (max_state - max_increment): #If there's room, increment by the max
      k = max_increment
    else: #If not, increment until max state is reached
      k = max_state - current_state
      
  # Case 2: Image is a little higher than current and we want to increment moderately
  elif (delta_S > 0) and (abs(delta_S) < max_increment):
    if current_state <= (max_state - delta_S): # If there's room, increment by the diff between imag eand current state
      k = delta_S
    else: #If not, increment until max state is reached
      k = max_state - current_state
  
  # Case 3: Image is much lower than current and we want to decrement as much as possible
  elif (delta_S < 0) and (abs(delta_S) >= max_increment):
    if current_state >= max_increment: #If there's room, decrement by the max
      k = -1*max_increment
    else: #If not, set to 0 (no negative states)
      k = -1*current_state 
  
  # Case 4: Image is a little lower than current and we want to decrement moderately
  elif (delta_S < 0) and (abs(delta_S) < max_increment):
    if current_state >= abs(delta_S): # If there's room, decrement by the diff between imag eand current state
      k = -1*abs(delta_S)
    else: #If not, decrement to 0
      k = -1*current_state
  
  # Case 5: Image and current are equal (shouldn't be reached for asynch)
  else:
    k = 0

  return k

def sync_update(num_states, image, new_state, current_state, max_state):
  max_increment=1 # We will only use 1 for max increment for synchronous
  for s_idx in range(num_states):
    delta_S = image[s_idx] - current_state[s_idx] # get the diff between image and current
    k = find_increment(max_increment, max_state, delta_S, current_state[s_idx])
    new_state[s_idx] = current_state[s_idx] + k
  return new_state


# This function takes in a perturbation vector k and returns the number of identical responses (so that it can be minimized)
def simulate(n_time_steps, M, perturbed_species={}, pert_start_time=0, post_pert_time_steps=0):
  
  # print("perturbation:", perturbed_species)
  
  #check for a non-zero pert_start_time
  if perturbed_species is not None:
    for perturbation in perturbed_species.values():
      start_time = perturbation[1] #this holds each pert's start time
      if start_time > pert_start_time: #this should get the max start time
        pert_start_time = start_time 
  

  full_trajectory = np.zeros((pert_start_time+n_time_steps+post_pert_time_steps+1,M.num_statevar),dtype=int)
  full_trajectory[0] = M.initial_state.copy()
  current_state = M.initial_state.copy()

  
  t = 0
  
  while t < pert_start_time+n_time_steps+post_pert_time_steps:
    
    new_state = np.full(M.num_statevar, -99) 
    image = np.zeros(M.num_statevar)

    # Set perturbation first if applicable
    for id, (level, start, duration) in perturbed_species.items():
      if start < t+1 <= start+duration:
        image[id] = level
        new_state[id] = level
        current_state[id] = level # Ensure this is held at the desired value
    

    # Find images of all except perturbed nodes
    for j, (source, target) in enumerate(zip(M.source_state_var_indices, M.target_state_var_indices)):
      source = source.item()
      target = target.item()
      skip = False
      
      for id, (level, start, duration) in perturbed_species.items():
        if (target == id) and (start < t+1 <= start+duration):
          #print("Continue. Target is ", target, "Id is ", id, "T is ", t)
          skip = True
          break # Perturbed species are already taken care of
      
      if skip:
        continue
      
      if M.thresholds_flag:
        image[target] += current_state[source]//M.thresholds[j]*M.weights[j]*M.polarities[j]
        # if target == 78 and (current_state[source]//M.thresholds[j]*M.weights[j]*M.polarities[j])!=0:
        #   print(f"j = {j}, image[{target}] = {image[target]}")
        #   print(f"j = {j}, source = {source}, current state = {current_state[source]}, threshold = {M.thresholds[j]}, weight = {M.weights[j]}, polarity = {M.polarities[j]}, addition = {current_state[source]//M.thresholds[j]*M.weights[j]*M.polarities[j]}")
      else:
        image[target] += current_state[source]*M.weights[j]*M.polarities[j]

    # Update state based on current state compared with image
    new_state = sync_update(M.num_statevar, image, new_state, current_state, M.max_state)
    #print("New state: ", new_state)
    current_state = new_state
    full_trajectory[t+1] = current_state # full trajectory holds entire solution for plotting

    t += 1

  return full_trajectory





