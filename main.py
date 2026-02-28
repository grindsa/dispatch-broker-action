#!/usr/bin/env python3
"""Dispatch GitHub Actions workflows in a repository, with option to exclude certain workflows."""
import argparse
from html import parser
import json
import requests


def get_workflows(token, repo, ref):
    """get all workflow files in a repo"""
    url = f"https://api.github.com/repos/{repo}/contents/.github/workflows"
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
    }
    params = {"ref": ref}

    # Make the request
    response = requests.get(url, headers=headers, params=params, timeout=10)
    response.raise_for_status()
    files = response.json()

    # Filter for .yml or .yaml files
    yaml_files = [
        f["name"]
        for f in files
        if f["type"] == "file"
        and (f["name"].endswith(".yml") or f["name"].endswith(".yaml"))
    ]
    return yaml_files


def dispatch_workflow(token, repo, ref, yaml_files, exclude_workflows, client_payload):
    """
    Dispatch workflows using the content from the specified ref (branch, tag, or SHA).
    The workflow will be executed as defined in that ref, not just the default branch.
    """
    url_template = (
        f"https://api.github.com/repos/{repo}/actions/workflows/{{}}/dispatches"
    )
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
    }
    payload = {"ref": ref, "inputs": json.loads(client_payload)}

    for yaml_file in yaml_files:
        if exclude_workflows and yaml_file in exclude_workflows:
            print(f"Skipping excluded workflow: {yaml_file}")
            continue

        url = url_template.format(yaml_file)
        response = requests.post(url, headers=headers, json=payload, timeout=10)

        if response.status_code == 204:
            print(f"Successfully dispatched workflow: {yaml_file}")
        else:
            print(
                f"Failed to dispatch workflow: {yaml_file}. Status code: {response.status_code}, Response: {response.text}"
            )


def main():
    """this is the main function"""
    parser = argparse.ArgumentParser(description="Dispatch a GitHub Actions workflow.")
    parser.add_argument(
        "--token", required=True, help="GitHub token with repo/workflow permissions"
    )
    parser.add_argument(
        "--repository", required=True, help="GitHub repository in the form owner/repo"
    )
    parser.add_argument("--ref", required=True, help="Git ref (branch, tag, or SHA)")
    parser.add_argument(
        "--client_payload", default="{}", help="JSON string of workflow inputs"
    )
    wf_grp = parser.add_mutually_exclusive_group(required=True)
    wf_grp.add_argument(
        "--workflows", default=None, help="workflows to include"
    )
    wf_grp.add_argument(
        "--exclude_workflows", default=None, help="workflows to exclude"
    )

    args = parser.parse_args()

    include_workflows = None
    exclude_workflows = None

    if args.workflows:
        include_workflows = [w.strip() for w in args.workflows.split(",")]
        exclude_workflows = None

    elif args.exclude_workflows:
        exclude_workflows = [w.strip() for w in args.exclude_workflows.split(",")]
        include_workflows = None

    if not include_workflows:
        # Get all workflow files
        yaml_files = get_workflows(args.token, args.repository, args.ref)
    else:
        yaml_files = include_workflows


    # Dispatch workflows
    dispatch_workflow(
        args.token,
        args.repository,
        args.ref,
        yaml_files,
        exclude_workflows,
        args.client_payload,
    )


if __name__ == "__main__":
    main()
