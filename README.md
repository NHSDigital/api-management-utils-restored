# api-management-utils
Scripts and utilities used across API managment platform and services 

## Scripts
* `template.py` - cli for basic jinja templating
* `test_pull_request_deployments.py` - cli for testing utils against other repositories
    * Environment Variables:
        * `AZURE_TOKEN` - Azure Devops token.
        * `NOTIFY_COMMIT_SHA` - Git Commit SHA that you want to report to.
        * `UTILS_PR_NUMBER` - The utils pull request number e.g. '123'
