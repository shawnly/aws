Setup Instructions

Save the Python script as create_codebuild.py in your repository.
Create the GitHub Actions workflow file at .github/workflows/create-codebuild.yml.
Set up the required secrets in your GitHub repository:

AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY
AWS_REGION
AWS_CODEBUILD_SERVICE_ROLE (The ARN of the IAM role for CodeBuild)
Note: GITHUB_TOKEN is automatically provided by GitHub Actions


Ensure AWS IAM permissions are set up correctly for the provided AWS credentials. The IAM user or role needs permissions to create and manage CodeBuild projects.

Usage
You can trigger this workflow manually through the GitHub UI:

Go to the "Actions" tab in your repository
Select the "Create AWS CodeBuild Project" workflow
Click "Run workflow"
Fill in the required parameters
Click "Run workflow" again

The workflow will execute your Python script with the provided parameters to create the AWS CodeBuild project.