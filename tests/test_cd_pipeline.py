from pathlib import Path


def test_service_template_uses_color_selector():
    data = Path("infra/helm/agent-services/templates/service.yaml").read_text()
    assert "color:" in data


def test_terraform_accepts_color_var():
    data = Path("infra/terraform/main.tf").read_text()
    assert "var.color" in data
