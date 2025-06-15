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

