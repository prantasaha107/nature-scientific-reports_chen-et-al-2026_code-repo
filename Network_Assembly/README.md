# Mtb-Macrophage cAMP Regulatory Network Pipeline
This repository contains the implementation of a mechanistically informed network model created de novo from prior knowledge and generative AI. The pipeline automates the extraction of molecular mediators from literature, assembles regulatory networks from curated databases, and uses a **Trustworthy Language Model (TLM)** to propose missing interactions.

## Methodology Overview
The project is divided into three primary functional modules, as described in the research paper and corresponding pseudo-code:
### 1. Identifying Molecular Mediators of Interest ###
This module extracts signaling molecules from expert-curated literature (e.g., Dey and Bishai, 2014).

  **Text Pre-processing**: Cleans raw OCR-extracted PDF text by removing page numbers, fixing hyphenation, and normalizing whitespace.
  
  **Named Entity Recognition (NER)**: Utilizes four domain-specific SciSpacy models (e.g., en_ner_jnlpba_md, en_ner_bionlp13cg_md) to identify candidate proteins.
  
  **Ontology Verification**: Candidate entities are cross-referenced against HGNC and UniProt databases via REST APIs to ensure standardized nomenclature.

### 2. Assembling a Regulatory Network De Novo ###
This module recovers documented interactions to build a baseline network.

  **Knowledge Retrieval**: Uses the INDRA framework to query PyBEL and Pathway Commons (BioPax) for interactions involving the verified proteins.
  
  **Regulatory Filtering**: Retains only specific interaction types: IncreaseAmount, DecreaseAmount, Activation, and Inhibition.
  
  **Graph Pruning**: Prunes "dead-end" nodes (sources and sinks) to produce a closed-loop architecture necessary for homeostatic stability.

### 3. Closing Regulatory Loops Using Hypothesis Generation ###
Since cAMP often lacks documented upstream regulators in standard databases, this module uses AI to propose missing links.

  **Part 3.1: Hypothesis Generation (TLM)**: Queries the Cleanlab Trustworthy Language Model (GPT-4 based) to predict bidirectional regulatory relationships between cAMP and other network nodes.
  
  **Part 3.2: Interaction Filtering (Otsu’s Method)**: Applies Otsu’s Method to the distribution of TLM trustworthiness scores to calculate an optimal threshold, separating reliable "foreground" predictions from untrustworthy "background" noise.

## Dependencies ##
  
1. **NER & NLP**: spaCy, SciSpacy, Tesseract OCR, Regex.
 
3. **Network Assembly**: INDRA, PyBEL, Pathway Commons.
 
5. **AI/LLM**: Cleanlab Studio API (Trustworthy Language Model), OpenAI GPT-4.
   
7. **Data Analysis**: Python (Pandas, NumPy, Matplotlib), Otsu’s Method implementation.
   

## Version Compatibility & Requirements ##
 **Note on Dependencies**: This pipeline was developed and tested using spacy==3.7.5 and numpy==1.26.4. These versions ensure full compatibility with the SciSpacy v0.5.4 models used in the NER phase (e.g., en_ner_jnlpba_md, en_ner_bc5cdr_md).
The may execute with more recent versions of these libraries but you may encounter deprecation warnings or log alerts due to API changes. For optimal stability we recommend using the versions specified in requirements.txt.If you choose to upgrade to the latest spacy and numpy releases, please ensure you also update the corresponding SciSpacy model versions to maintain structural compatibility.

 **Note on RAM requirements**: Please ensure that you have atleast 16GB of RAM in your system.
