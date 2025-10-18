"""Lightweight dashboard asset verification for hackathon demos."""

from pathlib import Path

import pytest


pytestmark = pytest.mark.manual


REQUIRED_PATHS = {
    "standalone.html": "Legacy standalone dashboard bundle",
    "standalone-refined.html": "Tailored refined static experience",
    "value_dashboard.html": "Value proposition snapshot",
    Path("app/page.tsx"): "Next.js dashboard entry point",
    Path("src/components/RefinedDashboard.tsx"): "Primary dashboard composition",
}


@pytest.fixture(scope="module")
def dashboard_dir() -> Path:
    """Return the dashboard directory under the repository root."""

    repo_root = Path(__file__).resolve().parents[2]
    directory = repo_root / "dashboard"
    assert directory.exists(), "Dashboard folder is missing"
    return directory


@pytest.mark.parametrize("path,description", REQUIRED_PATHS.items())
def test_required_dashboard_files_exist(dashboard_dir: Path, path: Path | str, description: str) -> None:
    """Ensure critical dashboard assets are present for the live demo."""

    relative_path = Path(path)
    filepath = dashboard_dir / relative_path
    assert filepath.exists(), f"{description} ({relative_path.as_posix()}) is missing"


def test_standalone_bundle_is_complete(dashboard_dir: Path) -> None:
    """Sanity check that the standalone bundle contains HTML and script content."""

    standalone = dashboard_dir / "standalone.html"
    content = standalone.read_text(encoding="utf-8")
    assert "</html>" in content.lower(), "Standalone bundle missing closing HTML"
    assert "<script" in content.lower(), "Standalone bundle missing inline scripts"
    assert len(content) > 30_000, "Standalone bundle appears truncated"
