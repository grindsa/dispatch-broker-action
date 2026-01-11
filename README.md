# Dispatch Broker Action

A GitHub Action to dispatch workflows via the GitHub API using a Python script.

## Usage

```yaml
- name: Dispatch Workflow
  uses: ./
  with:
    github_token: ${{ secrets.GITHUB_TOKEN }}
    workflow: 'ci.yml'
    ref: 'main'
    inputs: '{"param1": "value1"}'
```

## Inputs
- `github_token`: GitHub token with repo/workflow permissions (required)
- `workflow`: Workflow file name to dispatch (required)
- `ref`: Git ref (branch, tag, or SHA) to run the workflow on (required)
- `inputs`: JSON string of workflow inputs (optional)

## Development

- Install dependencies: `pip install -r requirements.txt`
- Run: `python main.py --github-token <token> --repo <owner/repo> --workflow <workflow.yml> --ref <branch> --inputs '{"key": "value"}'`
