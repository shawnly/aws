import boto3
import time
import sys
from datetime import datetime

def start_builds(project_name, number_of_builds):
    codebuild = boto3.client('codebuild')
    build_ids = []
    
    print(f"Starting {number_of_builds} builds...")
    for i in range(number_of_builds):
        try:
            response = codebuild.start_build(
                projectName=project_name,
                environmentVariablesOverride=[
                    {
                        'name': 'BUILD_NUMBER',
                        'value': str(i + 1),
                        'type': 'PLAINTEXT'
                    }
                ]
            )
            build_ids.append(response['build']['id'])
            print(f"Started build {i + 1}: {response['build']['id']}")
            # Add small delay between builds to prevent throttling
            time.sleep(1)
        except Exception as e:
            print(f"Error starting build {i + 1}: {str(e)}")
    
    return build_ids

def monitor_builds(build_ids):
    codebuild = boto3.client('codebuild')
    completed = set()
    
    print("\nMonitoring builds...")
    while len(completed) < len(build_ids):
        response = codebuild.batch_get_builds(ids=build_ids)
        
        for build in response['builds']:
            build_id = build['id']
            if build_id not in completed and build['buildStatus'] != 'IN_PROGRESS':
                completed.add(build_id)
                print(f"{datetime.now()}: Build {build_id} completed with status: {build['buildStatus']}")
        
        # Increased sleep time since Lambda builds might take longer to initialize
        time.sleep(15)
    
    print("\nAll builds completed!")

def main():
    if len(sys.argv) != 3:
        print("Usage: python test_builds.py <project_name> <number_of_builds>")
        sys.exit(1)
    
    project_name = sys.argv[1]
    number_of_builds = int(sys.argv[2])
    
    print(f"Testing Lambda-based CodeBuild project: {project_name}")
    build_ids = start_builds(project_name, number_of_builds)
    monitor_builds(build_ids)

if __name__ == "__main__":
    main()