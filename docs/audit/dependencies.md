# Dependency Audit

This document outlines the findings of the dependency audit, focusing on security vulnerabilities, license compliance, and outdated packages.

## 1. Methodology

Dependencies are primarily managed in `requirements.txt` and `constraints.txt`. The audit process involves:
*   Reviewing these files.
*   Using `pip-audit` to scan for known vulnerabilities.
*   Using `pip list --outdated` to identify packages that are not up-to-date.
*   Noting the existing automated dependency audit processes (e.g., via GitHub Actions).

The repository has automated checks for dependencies:
*   The `dependency-audit.yml` workflow runs `pip-audit` weekly and creates issues for vulnerabilities.
*   The `ci.yml` workflow also includes a step to run `pip-audit`.

## 2. Dependency Files

```txt
# requirements.txt
--extra-index-url https://download.pytorch.org/whl/cpu
pre-commit==4.2.0
pytest==8.0.0
pytest-cov==4.1.0
pytest-github-actions-annotate-failures==0.3.0
pytest-xdist==3.5.0
pydantic==2.6.4
pyyaml==6.0.1
requests==2.32.4
pdfplumber==0.10.2
pytesseract==0.3.10
Pillow==10.3.0
beautifulsoup4==4.13.4
readability-lxml==0.8.1
jsonschema==4.24.0
pykwalify==1.8.0
fastapi==0.110.0
uvicorn==0.27.0
opentelemetry-api==1.24.0
opentelemetry-sdk==1.24.0
opentelemetry-exporter-otlp==1.24.0
langchain==0.3.25
langgraph==0.0.24
langsmith==0.1.18
weaviate-client==3.26.7
googletrans==4.0.2
openai==1.3.5
trl==0.7.10
pytest-asyncio==0.23.6
torch==2.2.2
sentence-transformers==2.6.1
tenacity==8.2.3
datasets==3.6.0
lxml_html_clean==0.4.2
trafilatura==2.0.0
SQLAlchemy==2.0.29
asyncpg==0.29.0

```

```txt
# constraints.txt
pre-commit==4.2.0
pytest==8.0.0
pytest-cov==4.1.0
pytest-github-actions-annotate-failures==0.3.0
pytest-xdist==3.5.0
pydantic==2.6.4
pyyaml==6.0.1
requests==2.32.4
pdfplumber==0.10.2
pytesseract==0.3.10
Pillow==10.3.0
beautifulsoup4==4.13.4
readability-lxml==0.8.1
jsonschema==4.24.0
pykwalify==1.8.0
fastapi==0.110.0
uvicorn==0.27.0
opentelemetry-api==1.24.0
opentelemetry-sdk==1.24.0
opentelemetry-exporter-otlp==1.24.0
langchain==0.3.25
langgraph==0.0.24
langsmith==0.1.18
weaviate-client==3.26.7
googletrans==4.0.2
openai==1.3.5
trl==0.7.10
pytest-asyncio==0.23.6
torch==2.2.2+cpu
sentence-transformers==2.6.1
tenacity==8.2.3
datasets==3.6.0
lxml_html_clean==0.4.2
SQLAlchemy==2.0.29
asyncpg==0.29.0

```

## 3. Existing Vulnerability Report (`pip_audit_report.txt`)

An existing `pip_audit_report.txt` was found at the root of the repository, but it is empty.
A fresh scan will be performed next.

## 4. Vulnerability Scan (`pip-audit`)

Attempted to run a fresh `pip-audit` scan using the command `/home/swebot/.local/bin/pip-audit -r requirements.txt -f json --desc on --progress-spinner off`.
The scan failed during the process of creating a temporary virtual environment. The error indicates a problem with `ensurepip`:

```
Traceback (most recent call last):
  File "/home/swebot/.local/bin/pip-audit", line 8, in <module>
    sys.exit(audit())
  File "/home/swebot/.local/lib/python3.10/site-packages/pip_audit/_cli.py", line 538, in audit
    for spec, vulns in auditor.audit(source):
  File "/home/swebot/.local/lib/python3.10/site-packages/pip_audit/_audit.py", line 68, in audit
    for dep, vulns in self._service.query_all(specs):
  File "/home/swebot/.local/lib/python3.10/site-packages/pip_audit/_service/interface.py", line 155, in query_all
    for spec in specs:
  File "/home/swebot/.local/lib/python3.10/site-packages/pip_audit/_dependency_source/requirement.py", line 134, in collect
    yield from self._collect_from_files(collect_files)
  File "/home/swebot/.local/lib/python3.10/site-packages/pip_audit/_dependency_source/requirement.py", line 180, in _collect_from_files
    ve.create(ve_dir)
  File "/home/swebot/.local/lib/python3.10/site-packages/pip_audit/_virtual_env.py", line 80, in create
    return super().create(env_dir)
  File "/usr/lib/python3.10/venv/__init__.py", line 76, in create
    self._setup_pip(context)
  File "/usr/lib/python3.10/venv/__init__.py", line 329, in _setup_pip
    self._call_new_python(context, '-m', 'ensurepip', '--upgrade',
  File "/usr/lib/python3.10/venv/__init__.py", line 325, in _call_new_python
    subprocess.check_output(args, **kwargs)
  File "/usr/lib/python3.10/subprocess.py", line 421, in check_output
    return run(*popenargs, stdout=PIPE, timeout=timeout, check=True,
  File "/usr/lib/python3.10/subprocess.py", line 526, in run
    raise CalledProcessError(retcode, process.args,
subprocess.CalledProcessError: Command '['/tmp/tmpcbzbl5ih/bin/python', '-m', 'ensurepip', '--upgrade', '--default-pip']' returned non-zero exit status 1.
```

This failure is likely due to the previously encountered "No space left on device" error, preventing the creation of necessary temporary environments for the scan. Therefore, no vulnerability report could be generated in this audit.
The `dependency-audit.yml` workflow in CI should be consulted for vulnerability reports.

## 5. Outdated Packages (`pip list --outdated`)

Attempted to check for outdated packages. The process involves first trying to install dependencies from `requirements.txt` to get an accurate list.
The command `pip install -r requirements.txt -c constraints.txt` failed. The output included dependency resolver errors (e.g., `poetry 2.1.0 requires packaging>=24.0, but you have packaging 23.2 which is incompatible.`) and indicated that `/home/swebot/.local/bin/pip` was not found for a subsequent step.

Therefore, an accurate list of outdated packages could not be generated. This is likely due to a combination of the dependency conflicts and potentially the "No space left on device" error preventing full resolution and installation of dependencies.

## 6. Recommendations

*   **Monitor Vulnerabilities:** Regularly review the output of the `dependency-audit.yml` workflow and address any reported vulnerabilities promptly by updating packages or applying mitigations.
*   **Update Outdated Packages:** Periodically review the list of outdated packages and update them, especially those with significant version differences or known security/bug fixes. Test thoroughly after updates. (Note: This audit could not generate this list due to environment issues).
*   **License Compliance:** While `pip-audit` can report licenses, a more thorough license compliance check might involve tools like `pip-licenses` or manual review if strict compliance is required for distribution. For this audit, we rely on `pip-audit`'s license output (which could not be generated).
*   **Review `constraints.txt`:** Ensure `constraints.txt` is actively maintained and reflects true, tested compatibility constraints. Remove constraints that are no longer necessary.
*   **Resolve Environment Issues:** The "No space left on device" error and dependency conflicts (e.g., `packaging` version) encountered during this audit need to be resolved in the execution environment. This is critical for reliable CI checks and future audits.
*   **Investigate `pip` Path Issue:** The error ` /home/swebot/.local/bin/pip: No such file or directory` when trying to list outdated packages (after `pip install` failed) should be investigated. Ensure `pip` is consistently available and on the PATH.
