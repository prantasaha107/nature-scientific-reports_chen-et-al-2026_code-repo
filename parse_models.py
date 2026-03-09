import numpy as np
import ast
import pandas as pd

class ModelData:
  def __init__(self, num_relations, num_statevar, max_state, source_state_var_indices, target_state_var_indices, weights, polarities, thresholds_flag, initial_state, thresholds, species_names):
    self.num_relations = num_relations
    self.num_statevar = num_statevar
    self.max_state = max_state
    self.source_state_var_indices = source_state_var_indices
    self.target_state_var_indices = target_state_var_indices
    self.weights = weights
    self.polarities = polarities
    self.initial_state = initial_state
    self.thresholds_flag = thresholds_flag
    if thresholds_flag:
      self.thresholds = thresholds
    else:
      self.thresholds = None
    self.species_names = species_names


def read_model_data(sourceTarget_file, models_file, max_state, thresholds_flag, model_num):
  
  # Read source/target file for parsing 
  known_relations = pd.read_excel(sourceTarget_file,sheet_name="Relations",header=0,index_col=None,usecols="A:E",engine='openpyxl')
  node_list = pd.read_excel(sourceTarget_file,sheet_name="SS_Constraints",header=0,index_col=None,usecols="A:E",engine='openpyxl')
  all_models = pd.read_csv(models_file)
  model = all_models.iloc[[model_num]]

  num_relations = len(known_relations) # Number of relations in original input network
  num_statevar = len(node_list.index) # Number of state variables/nodes



  # Read in source/target state variable indices
  source_state_var_indices=np.ones((num_relations,1),dtype='int')
  target_state_var_indices=np.ones((num_relations,1),dtype='int')
  for k in range(0,num_statevar):
    # find state var k name with state var index
    for r in range(0,num_relations):
      if known_relations.source[r]==node_list.node[k]:
        source_state_var_indices[r]=k
      if known_relations.target[r]==node_list.node[k]:
        target_state_var_indices[r]=k
  
  # Read in dictionary mapping index to node name while we're at it
  species_names = dict(zip(node_list.index, node_list.node))

  # Read in weights
  weights = model["relations weight w"].apply(ast.literal_eval).tolist()  # Convert strings to lists
  weights = np.array(weights)  # Convert to a NumPy array
  weights = weights.flatten()
  # print(weights.shape)
  # print("Weights:", weights)

  #Read in polarities
  polarities = model["relations polarity"].apply(ast.literal_eval).tolist()  # Convert strings to lists
  polarities = np.array(polarities)  # Convert to a NumPy array
  polarities = polarities.flatten()

  # Read in threshold here (if applicable)
  if thresholds_flag:
    thresholds = model["relations thresholds"].apply(ast.literal_eval).tolist()
    thresholds = np.array(thresholds)
    thresholds= thresholds.flatten()
  else:
    thresholds = None
  

  initial_state = []
  initial_state = (np.array(node_list.C1,dtype='int')).copy()


  
  return ModelData(num_relations=num_relations, num_statevar=num_statevar, max_state=max_state, 
                   source_state_var_indices=source_state_var_indices, target_state_var_indices=target_state_var_indices, 
                   weights=weights, polarities=polarities, thresholds_flag=thresholds_flag, initial_state=initial_state, 
                   thresholds=thresholds, species_names=species_names)  #Everything is packaged into a ModelData object
