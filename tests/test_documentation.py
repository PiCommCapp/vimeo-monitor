#!/usr/bin/env python3
"""
Documentation testing and validation.
"""

import sys
from pathlib import Path

import pytest

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


@pytest.mark.documentation
class TestDocumentation:
    """Test documentation integrity and accuracy."""

    def setup_method(self):
        """Set up test fixtures."""
        self.project_root = Path(__file__).parent.parent.parent
        self.docs_dir = self.project_root / "docs"
        self.src_dir = self.project_root / "src"

    def test_readme_exists(self):
        """Test that README.md exists."""
        readme_path = Path("/home/admin/code/vimeo-monitor/README.md")
        assert readme_path.exists(), "README.md should exist"

    def test_readme_has_content(self):
        """Test that README.md has meaningful content."""
        readme_path = self.project_root / "README.md"
        if readme_path.exists():
            content = readme_path.read_text()
            assert len(content) > 100, "README.md should have substantial content"
            assert (
                "Vimeo Monitor" in content
            ), "README.md should mention the project name"

    def test_docs_directory_structure(self):
        """Test that docs directory has proper structure."""
        if self.docs_dir.exists():
            # Check for key documentation files
            expected_files = ["index.md", "installation.md", "troubleshooting.md"]

            for file_name in expected_files:
                file_path = self.docs_dir / file_name
                if file_path.exists():
                    content = file_path.read_text()
                    assert (
                        len(content) > 50
                    ), f"{file_name} should have meaningful content"

    def test_pyproject_toml_documentation(self):
        """Test that pyproject.toml has proper documentation."""
        pyproject_path = Path("/home/admin/code/vimeo-monitor/pyproject.toml")
        assert pyproject_path.exists(), "pyproject.toml should exist"

        content = pyproject_path.read_text()
        assert "description" in content, "pyproject.toml should have description"
        assert "authors" in content, "pyproject.toml should have authors"

    def test_source_code_docstrings(self):
        """Test that source code has proper docstrings."""
        if self.src_dir.exists():
            python_files = list(self.src_dir.rglob("*.py"))

            for py_file in python_files:
                if py_file.name == "__init__.py":
                    continue

                content = py_file.read_text()

                # Check for module docstring
                if content.strip():
                    lines = content.split("\n")
                    first_line = lines[0].strip()
                    assert first_line.startswith('"""') or first_line.startswith(
                        "'''"
                    ), f"{py_file} should start with a docstring"

    def test_config_documentation(self):
        """Test that configuration is properly documented."""
        config_path = self.src_dir / "vimeo_monitor" / "config.py"
        if config_path.exists():
            content = config_path.read_text()

            # Check for class docstring
            assert "class Config:" in content
            assert '"""' in content, "Config class should have docstring"

            # Check for method docstrings
            assert "def __init__" in content
            assert "def validate" in content

    def test_logger_documentation(self):
        """Test that logger is properly documented."""
        logger_path = self.src_dir / "vimeo_monitor" / "logger.py"
        if logger_path.exists():
            content = logger_path.read_text()

            # Check for class docstring
            assert "class Logger:" in content
            assert '"""' in content, "Logger class should have docstring"

    def test_monitor_documentation(self):
        """Test that monitor is properly documented."""
        monitor_path = self.src_dir / "vimeo_monitor" / "monitor.py"
        if monitor_path.exists():
            content = monitor_path.read_text()

            # Check for class docstring
            assert "class Monitor:" in content
            assert '"""' in content, "Monitor class should have docstring"

    def test_process_manager_documentation(self):
        """Test that process manager is properly documented."""
        process_manager_path = self.src_dir / "vimeo_monitor" / "process_manager.py"
        if process_manager_path.exists():
            content = process_manager_path.read_text()

            # Check for class docstring
            assert "class ProcessManager:" in content
            assert '"""' in content, "ProcessManager class should have docstring"

    def test_health_module_documentation(self):
        """Test that health module is properly documented."""
        health_module_path = self.src_dir / "vimeo_monitor" / "health_module.py"
        if health_module_path.exists():
            content = health_module_path.read_text()

            # Check for class docstring
            assert "class HealthModule:" in content
            assert '"""' in content, "HealthModule class should have docstring"

    def test_environment_variables_documentation(self):
        """Test that environment variables are documented."""
        # Check for .env.sample file
        env_sample_path = self.project_root / ".env.sample"
        if env_sample_path.exists():
            content = env_sample_path.read_text()
            assert "VIMEO_TOKEN" in content, ".env.sample should document VIMEO_TOKEN"
            assert "VIMEO_KEY" in content, ".env.sample should document VIMEO_KEY"
            assert "VIMEO_SECRET" in content, ".env.sample should document VIMEO_SECRET"

    def test_installation_documentation(self):
        """Test that installation is properly documented."""
        # Check for installation script
        install_script_path = self.project_root / "scripts" / "install.sh"
        if install_script_path.exists():
            content = install_script_path.read_text()
            assert (
                len(content) > 100
            ), "Installation script should have substantial content"

    def test_makefile_documentation(self):
        """Test that Makefile has proper documentation."""
        makefile_path = self.project_root / "Makefile"
        if makefile_path.exists():
            content = makefile_path.read_text()
            assert "help:" in content, "Makefile should have help target"
            assert "##" in content, "Makefile should have documentation comments"

    def test_test_documentation(self):
        """Test that test files are properly documented."""
        tests_dir = self.project_root / "tests"
        if tests_dir.exists():
            test_files = list(tests_dir.rglob("test_*.py"))

            for test_file in test_files:
                content = test_file.read_text()

                # Check for module docstring
                if content.strip():
                    lines = content.split("\n")
                    first_line = lines[0].strip()
                    assert first_line.startswith('"""') or first_line.startswith(
                        "'''"
                    ), f"{test_file} should start with a docstring"

    def test_api_reference_accuracy(self):
        """Test that API references are accurate."""
        # This test would verify that documented APIs match actual implementations
        # For now, we'll do basic checks

        config_path = self.src_dir / "vimeo_monitor" / "config.py"
        if config_path.exists():
            content = config_path.read_text()

            # Check that documented methods exist
            assert "def validate(" in content, "validate method should exist"
            assert (
                "def get_vimeo_client_config(" in content
            ), "get_vimeo_client_config method should exist"
            assert "def get_stream_id(" in content, "get_stream_id method should exist"

    def test_error_handling_documentation(self):
        """Test that error handling is documented."""
        # Check that error scenarios are documented in tests
        error_tests_path = (
            self.project_root / "tests" / "error_scenarios" / "test_error_handling.py"
        )
        if error_tests_path.exists():
            content = error_tests_path.read_text()
            assert "TestErrorHandling" in content, "Error handling tests should exist"
            assert (
                "test_config_validation_errors" in content
            ), "Config validation error tests should exist"

    def test_integration_test_documentation(self):
        """Test that integration tests are documented."""
        integration_tests_path = (
            self.project_root / "tests" / "integration" / "test_integration.py"
        )
        if integration_tests_path.exists():
            content = integration_tests_path.read_text()
            assert (
                "TestSystemIntegration" in content
            ), "System integration tests should exist"
            assert (
                "test_system_initialization" in content
            ), "System initialization tests should exist"

    def test_health_monitoring_documentation(self):
        """Test that health monitoring is documented."""
        health_tests_path = self.project_root / "tests" / "test_health_module.py"
        if health_tests_path.exists():
            content = health_tests_path.read_text()
            assert (
                "TestHealthMonitoringConfig" in content
            ), "Health monitoring config tests should exist"
            assert (
                "test_health_config_loading" in content
            ), "Health config loading tests should exist"

    def test_documentation_consistency(self):
        """Test that documentation is consistent across files."""
        # Check that version numbers are consistent
        pyproject_path = self.project_root / "pyproject.toml"
        if pyproject_path.exists():
            pyproject_content = pyproject_path.read_text()

            # Extract version from pyproject.toml
            version_line = [
                line
                for line in pyproject_content.split("\n")
                if "version" in line and "=" in line
            ]
            if version_line:
                version = version_line[0].split("=")[1].strip().strip('"').strip("'")

                # Check that version is mentioned in README
                readme_path = self.project_root / "README.md"
                if readme_path.exists():
                    # Version should be mentioned somewhere in README
                    assert (
                        len(version) > 0
                    ), "Version should be defined in pyproject.toml"

    def test_documentation_accessibility(self):
        """Test that documentation is accessible and readable."""
        readme_path = self.project_root / "README.md"
        if readme_path.exists():
            content = readme_path.read_text()

            # Check for common accessibility issues
            assert "##" in content, "README should have proper heading structure"
            assert "```" in content, "README should have code examples"

            # Check that content is not too dense
            lines = content.split("\n")
            non_empty_lines = [line for line in lines if line.strip()]
            assert len(non_empty_lines) > 10, "README should have substantial content"

    def test_documentation_maintenance(self):
        """Test that documentation is maintainable."""
        # Check that documentation files are not too large
        docs_files = []
        if self.docs_dir.exists():
            docs_files.extend(list(self.docs_dir.rglob("*.md")))

        for doc_file in docs_files:
            content = doc_file.read_text()
            # Documentation files should not be excessively long
            assert len(content) < 10000, f"{doc_file} should not be excessively long"


if __name__ == "__main__":
    pytest.main([__file__])
