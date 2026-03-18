# Simulation code for "A Regulatory Network Informed Investigation of macrophage cAMP dynamics during Mycobacterium tuberculosis infection" 

Codes used for parameter identification and simulated perturbations in the paper "A Regulatory Network Informed Investigation of macrophage cAMP dynamics during Mycobacterium tuberculosis infection" by Chris Chen, Pranta Saha, Joyce Reimer, Shaun Wachter, Jeff Chen, Gordon Broderick, and Neeraj Dhar.

## Contents
* MTb regulatory network file: `MTb_network-Chen_et_al_2026.xlsx`
* Parameter identification via constraint satisfaction: `parameter_logic_identification.py`
* File with 100 candidate models (from parameter identification code): `models_out_example.csv`
* Simulation code: `main.py`, `parse_models.py`, `simulate.py`, `plot.py`

## Dependencies
* python==3.12.3
* cpmpy==0.9.23
* numpy==2.4.3
* openpyxl==3.1.5
* pandas==3.0.1
* matplotlib==3.10.8

## Instructions

To generate a plot of any combination of model number, perturbed node, perturbation duration (i.e. transient pulse or continuous), and measured node, change any of these 4 parameters at the top of `main.py`, then run `python3 main.py`.

For parameter identification code, run `python3 parameter_logic_identification.py`.