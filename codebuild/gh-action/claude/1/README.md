python create-codebuild-updated.py \
  --github-org "your-org-name" \
  --github-token "your-github-pat-token" \
  --aws-region "us-east-1" \
  --codebuild-project-name "your-project-name" \
  --vpc-id "vpc-12345" \
  --subnet-ids "subnet-12345,subnet-67890" \
  --security-group-id "sg-12345" \
  --service-role "arn:aws:iam::123456789012:role/YourCodeBuildRole" \
  --github-domain "github.com"

  # AWS CodeBuild Project Creator

This project contains a Python script (`create-codebuild.py`) that creates an AWS CodeBuild project and saves the webhook info to a file for GitHub integration.

---

## 🧰 Prerequisites

- macOS
- Python 3.7+ installed (`python3 --version`)
- AWS CLI configured (`aws configure`)
- GitHub personal access token (stored as a GitHub secret)

---

## 🐍 Set Up Python Environment (macOS)

### 1. Clone this repository

```bash
git clone https://github.com/your-repo/codebuild-creator.git
cd codebuild-creator
```

### 2. Create a Python virtual environment

```bash
python3 -m venv .venv
```

### 3. Activate the virtual environment

```bash
source .venv/bin/activate
```

You should now see `(.venv)` at the start of your terminal prompt.

### 4. Install required packages

```bash
pip install boto3
```

---

## ▶️ Run the Script

Make sure your AWS credentials and GitHub token are accessible (via environment variables or passed as input).

```bash
python create-codebuild.py \
  --project-name my-project \
  --source-type GITHUB \
  --github-org my-org \
  --vpc-id vpc-xxxxxxx \
  --subnets subnet-12345,subnet-67890 \
  --security-groups sg-12345678 \
  --compute-type BUILD_GENERAL1_SMALL \
  --service-role arn:aws:iam::123456789012:role/CodeBuildRole \
  --github-token $CODEBUILD_GITHUB_TOKEN
```

---

## 📁 Output

The script will generate a webhook info file in the `output/` folder:

```
output/codebuild-webhook-info-my-project.txt
```

This file contains:

- GitHub webhook URL
- Webhook secret

You can manually paste this info into your GitHub repository's Webhooks settings.

---

## 💡 Deactivate the Virtual Environment

When you're done:

```bash
deactivate
```
