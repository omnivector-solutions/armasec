import pytest

try:
    import typer  # noqa
except ImportError:
    pytest.skip("CLI extra is not installed", allow_module_level=True)
