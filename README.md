# Automatic Metadata Extraction

This repository contains code and resources for automatic metadata extraction from software repositories, developed as part of my thesis. The project involves finetuning the Llama 3.1 8b model on custom dataset to extract metadata from software repositories and compare results with existing approaches.

## Project Overview

This project aims to automate the extraction of metadata from software repositories by leveraging Large Language Models (LLMs). The project extracts important repository information, including READMEs, dependencies, and CodeMeta files, processes this data to create a custom dataset. After extracting repository files, the dataset is annotated with these elements:

- softwareRequirements
- buildInstructions
- author
- contributor
- funder
- identifier
- license
- keywords

This annotated dataset is then used to fine-tune the Llama 3.1 8b model for metadata extraction. The performance is then compared against existing tools like SOMEF (Software Metadata Extraction Framework).

## Repository Structure

```
automatic-metadata-extraction/
├── data_extraction/                # Scripts to collect repository data
│   ├── get_repo_files.py           # Extract content from GitHub/GitLab repos
│   └── scrape_repo_links.py        # Web scraping for repository links
├── dataset/                        # Extracted and annotated metadata
│   ├── compare_results.csv         # Comparison between methods
│   └── dataset_alpaca_style.csv    # Annotated dataset for LLM training
├── viz/                            # Visualization tools
│   ├── LLM_eval_viz/               # Evaluation visualizations
│   │   ├── result/                 # Results directory
│   │   ├── training_analysis_summary.txt
│   │   └── training_viz.py         # Training evaluation plots
│   └── LLM_vs_SOMEF_viz/           # Comparison visualizations
│       ├── element_result/         # Element-wise comparison results
│       ├── repo_result/            # Repository-wise comparison results
│       ├── element_comp.py         # Element-wise comparison script
│       └── repo_comp.py            # Repository-wise comparison script
├── colabs/                         # Jupyter notebooks
│   ├── llm_inference.ipynb         # LLM-based extraction notebooks
│   ├── finetuning_llama.ipynb      # LLM model fine-tuning notebook
│   └── test_multiple_repos.csv     # Test dataset for model evaluation
└── requirements.txt                # Python dependencies
```

## Components

### Data Extraction

- **scrape_repo_links.py**: Scrapes GitHub and GitLab links from the Helmholtz Software website to create a dataset of software repositories for analysis.
- **get_repo_files.py**: Uses GitHub and GitLab APIs to extract READMEs, dependency files, and CodeMeta files from repositories. Performs preprocessing and formatting of the extracted data.

### Dataset

- **dataset_alpaca_style.csv**: The cleaned and annotated dataset after the extraction process.
- **compare_results.csv**: Contains comparison results used for post-training analysis.

### Model Training and Inference

- **finetuning_llama.ipynb**: Jupyter notebook containing all the instructions and code needed to fine-tune the Llama 3.1 8b model on the custom dataset using UnSloth and save it to the Hugging Face Hub.
- **llm_inference.ipynb**: Used to perform inference with the fine-tuned model from Hugging Face.
- **test_multiple_repos.csv**: Test dataset to evaluate the performance of the fine-tuned Llama model on multiple repository data.

### Visualization

- **LLM_eval_viz/**:
  - **training_viz.py**: Generates plots visualizing the evaluation metrics of the fine-tuned model.
  
- **LLM_vs_SOMEF_viz/**:
  - **repo_comp.py**: Compares the results of LLM-based extraction and SOMEF by repository-wise.
  - **element_comp.py**: Compares the results of LLM-based extraction and SOMEF by element-wise.

## Installation

1. Clone this repository:
```bash
git clone https://github.com/smutyala1at/automatic-metadata-extraction.git
cd automatic-metadata-extraction
```

2. Create a virtual environment (recommended):
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

> **Note:** The dataset is already prepared and available in `dataset/dataset_alpaca_style.csv`. You can skip the data extraction steps and start directly from the model fine-tuning process using this prepared dataset. The dataset can also be used for fine-tuning other models beyond Llama 3.1 8b.

### Data Extraction (Optional)

The following steps are only needed if you want to recreate the dataset from scratch:

To extract repository links:
```bash
python3 data_extraction/scrape_repo_links.py
```

To extract repository files:
```bash
python3 data_extraction/get_repo_files.py
```

### Model Fine-tuning

Open the `colabs/finetuning_llama.ipynb` notebook in a Jupyter environment with GPU access and follow the instructions to fine-tune the Llama 3.1 8b model on the prepared dataset. The notebook contains all necessary steps and explanations for the fine-tuning process.

### Inference

After fine-tuning, use the `colabs/llm_inference.ipynb` notebook to perform inference with the fine-tuned model. You can use `test_multiple_repos.csv` to evaluate model performance.

### Visualization

To generate training evaluation visualizations:
```bash
python3 viz/LLM_eval_viz/training_viz.py
```

To compare LLM and SOMEF results:
```bash
python3 viz/LLM_vs_SOMEF_viz/repo_comp.py  # Repository-wise comparison
python3 viz/LLM_vs_SOMEF_viz/element_comp.py  # Element-wise comparison
```

## Results

The visualizations generated in the `viz/` directory provide insights into:
1. Training performance of the fine-tuned model
2. Comparison between LLM-based extraction and SOMEF methods
3. Analysis of extraction performance for different metadata elements