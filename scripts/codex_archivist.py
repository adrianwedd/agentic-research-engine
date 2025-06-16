import argparse

from scripts import issue_logger


def main(argv=None):
    parser = argparse.ArgumentParser(description="Post worklog to closed issue")
    parser.add_argument("--repo", required=True)
    parser.add_argument("--issue", type=int, required=True)
    parser.add_argument("--worklog", required=True)
    args = parser.parse_args(argv)

    issue_url = f"{issue_logger.GITHUB_API}/repos/{args.repo}/issues/{args.issue}"
    data = issue_logger._load_worklog(args.worklog)
    url = issue_logger.post_worklog_comment(issue_url, data)
    if not url:
        return 1
    print(f"Posted worklog to {url}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
