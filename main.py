#!/usr/bin/env python3
"""Dispatch GitHub Actions workflows in a repository, with option to exclude certain workflows."""
import argparse
import json
import sys
import time

import requests

REQUEST_TIMEOUT = 30
MAX_ATTEMPTS = 3
RETRY_BACKOFF_SECONDS = 2


def _request_with_retries(method, url, **kwargs):
    """HTTP request with retries for timeouts and 5xx responses."""
    kwargs.setdefault("timeout", REQUEST_TIMEOUT)
    last_exc = None
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            response = requests.request(method, url, **kwargs)
            if response.status_code >= 500 and attempt < MAX_ATTEMPTS:
                print(
                    f"Transient HTTP {response.status_code} for {method.upper()} {url} "
                    f"(attempt {attempt}/{MAX_ATTEMPTS}); retrying..."
                )
                time.sleep(RETRY_BACKOFF_SECONDS * attempt)
                continue
            return response
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as exc:
            last_exc = exc
            if attempt >= MAX_ATTEMPTS:
                raise
            print(
                f"Transient {type(exc).__name__} for {method.upper()} {url} "
                f"(attempt {attempt}/{MAX_ATTEMPTS}); retrying..."
            )
            time.sleep(RETRY_BACKOFF_SECONDS * attempt)
    if last_exc is not None:
        raise last_exc
    raise RuntimeError(f"request failed without response: {method.upper()} {url}")


def get_workflows(token, repo, ref):
    """get all workflow files in a repo"""
    url = f"https://api.github.com/repos/{repo}/contents/.github/workflows"
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
    }
    params = {"ref": ref}

    response = _request_with_retries("get", url, headers=headers, params=params)
    response.raise_for_status()
    files = response.json()

    yaml_files = [
        f["name"]
        for f in files
        if f["type"] == "file"
        and (f["name"].endswith(".yml") or f["name"].endswith(".yaml"))
    ]
    return yaml_files


def _is_missing_dispatch_trigger(status_code, body):
    """True when GitHub rejects dispatch because the workflow has no workflow_dispatch."""
    if status_code != 422:
        return False
    return "workflow_dispatch" in body


def dispatch_workflow(token, repo, ref, yaml_files, exclude_workflows, client_payload):
    """
    Dispatch workflows using the content from the specified ref (branch, tag, or SHA).
    The workflow will be executed as defined in that ref, not just the default branch.
    Returns the number of hard failures (timeouts / unexpected status codes).
    """
    url_template = (
        f"https://api.github.com/repos/{repo}/actions/workflows/{{}}/dispatches"
    )
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
    }
    payload = {"ref": ref, "inputs": json.loads(client_payload)}
    hard_failures = 0

    for yaml_file in yaml_files:
        if yaml_file.startswith("_"):
            print(f"Skipping reusable/partial workflow: {yaml_file}", flush=True)
            continue

        if exclude_workflows and yaml_file in exclude_workflows:
            print(f"Skipping excluded workflow: {yaml_file}", flush=True)
            continue

        url = url_template.format(yaml_file)
        try:
            response = _request_with_retries(
                "post", url, headers=headers, json=payload
            )
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as exc:
            print(
                f"Failed to dispatch workflow: {yaml_file}. "
                f"{type(exc).__name__}: {exc}",
                flush=True,
            )
            hard_failures += 1
            continue

        if response.status_code == 204:
            print(f"Successfully dispatched workflow: {yaml_file}", flush=True)
        elif _is_missing_dispatch_trigger(response.status_code, response.text):
            print(
                f"Skipping workflow without workflow_dispatch: {yaml_file}",
                flush=True,
            )
        else:
            print(
                f"Failed to dispatch workflow: {yaml_file}. "
                f"Status code: {response.status_code}, Response: {response.text}",
                flush=True,
            )
            hard_failures += 1

    return hard_failures


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
    wf_grp.add_argument("--workflows", default=None, help="workflows to include")
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
        yaml_files = get_workflows(args.token, args.repository, args.ref)
    else:
        yaml_files = include_workflows

    hard_failures = dispatch_workflow(
        args.token,
        args.repository,
        args.ref,
        yaml_files,
        exclude_workflows,
        args.client_payload,
    )
    if hard_failures:
        print(f"Dispatch finished with {hard_failures} hard failure(s).", flush=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
