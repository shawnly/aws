# setup environment
Step 1: Install Python 3 via Homebrew
mkdir my_project
cd my_project
python -m venv venv

source venv/bin/activate
pip install requests
deactivate

pip install -r requirements.txt

Option 2: Use conda for package management
Conda handles binary dependencies better than pip in many cases:

# Install miniconda
brew install --cask miniconda

# Create a conda environment
conda create -n aws-cost python=3.11
conda activate aws-cost

# Install the packages
conda install pandas matplotlib openpyxl boto3

python aws-cost-png.py --start-date 2023-01-01 --end-date 2023-12-31