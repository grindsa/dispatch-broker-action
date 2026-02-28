
# Dispatch Broker Action

## Overview

Dispatch Broker Action is a GitHub Action designed to automate the dispatching of workflows via the GitHub API using Python. It enables flexible orchestration and integration with other workflows or external systems, making CI/CD pipelines more dynamic and customizable.

## Features

- Trigger workflows programmatically
- Pass custom inputs to workflows
- Integrate with other GitHub Actions
- Simple setup and configuration

## Requirements

- Python 3.8+
- GitHub Actions environment

## Setup

1. **Clone the repository:**

   ```bash
   git clone https://github.com/grindsa/dispatch-broker-action.git
   cd dispatch-broker-action
   ```

2. **(Optional) Create and activate a virtual environment:**

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

## Usage

Add the action to your workflow:

```yaml
jobs:
  dispatch:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v3
      - name: Dispatch Workflow
        uses: grindsa/dispatch-broker-action@main
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          workflow: 'ci.yml'
          ref: 'main'
          inputs: '{"param1": "value1"}'
```

### Inputs

- `github_token`: GitHub token with repo/workflow permissions (**required**)
- `workflow`: Workflow file name to dispatch (**required**)
- `ref`: Git ref (branch, tag, or SHA) to run the workflow on (**required**)
- `inputs`: JSON string of workflow inputs (**optional**)

## Configuration

Configure the action by providing the required inputs in your workflow. Example:

```yaml
with:
  github_token: ${{ secrets.GITHUB_TOKEN }}
  workflow: 'ci.yml'
  ref: 'main'
  inputs: '{"param1": "value1"}'
```

## Development

To run the main script locally:

```bash
python main.py --github-token <token> --repo <owner/repo> --workflow <workflow.yml> --ref <branch> --inputs '{"key": "value"}'
```

## Contributing

Contributions are welcome! Please open issues or submit pull requests for improvements or bug fixes.

## License

This project is licensed under the terms of the MIT License. See [LICENSE](LICENSE) for details.
