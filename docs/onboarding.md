# Onboarding Guide

This guide helps new contributors set up the development environment quickly.

## Quick Start
1. Clone the repository and enter the project directory.
   ```bash
   git clone <repository-url>
   cd agentic-research-engine
   ```
2. Install core Python dependencies using the minimal bootstrap script.
   ```bash
   bash scripts/bootstrap_minimal.sh
   ```
  For the full toolchain (including pre-commit hooks) run `bash scripts/agent-setup.sh` instead.
  The setup script installs packages using the pre-generated `constraints.txt` file
  to ensure deterministic versions and avoid pip resolver loops.

## Minimal Setup
For a lightweight environment, you can run only the minimal bootstrap script:
```bash
bash scripts/bootstrap_minimal.sh
```

The script installs the core dependencies while respecting environment variables
like `HTTP_PROXY`, `HTTPS_PROXY`, and `CUDA_VISIBLE_DEVICES` for proxy routing
and GPU selection. Use this when you don't need the full toolchain.

## Embedding Cache
The episodic memory service keeps an in-memory LRU cache so identical text
chunks aren't embedded more than once. Control the cache size with the
`EMBED_CACHE_SIZE` environment variable—set it to `0` to disable caching or a
positive number to specify how many distinct chunks to remember.

Larger cache sizes reduce retrieval latency at the cost of memory usage. In
local testing a cache of 512 entries improved P95 latency by roughly 15%. For
additional performance variables such as `VECTOR_SEARCH_WORKERS` see
`docs/performance.md`.

## Link Checker
Validate links in Markdown files with the link checker script, which wraps the
[`lychee`](https://github.com/lycheeverse/lychee) link checker:

```bash
python scripts/link_check.py
```
Run this before submitting a pull request to catch any broken documentation
links. The setup script installs `lychee` automatically using `cargo`. If you
need to install it manually, run:

```bash
cargo install lychee --locked --version 0.13.0
```

## Troubleshooting

### pip network timeouts
- Use a mirror if you experience slow downloads:
  ```bash
  pip install -r requirements.txt -i https://pypi.org/simple --timeout 100
  ```
- Increase the default timeout with `--default-timeout=100`.
- Configure `HTTP_PROXY` and `HTTPS_PROXY` when behind a corporate firewall.

### Docker setup tips
- Verify Docker is installed and the daemon is running:
  ```bash
  docker info
  ```
- If using a proxy, set it for Docker via `~/.docker/config.json` or environment variables.
- On Linux, ensure volume mounts use absolute paths and your user is in the `docker` group.

### GPU environment prerequisites
- Install the latest NVIDIA drivers and confirm with `nvidia-smi`.
- CUDA 11.8 or newer is recommended for GPU acceleration.
- Match the CUDA version with any local PyTorch or TensorFlow builds if used.
- Set `CUDA_VISIBLE_DEVICES` to control which GPU the processes use.

