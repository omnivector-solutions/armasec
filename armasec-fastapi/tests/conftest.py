import pytest

from armasec_core.schemas import DomainConfig


@pytest.fixture()
def rs256_secondary_domain_config():
    """
    Return the DomainConfig model for the default rs256 domain.
    """
    return DomainConfig(domain="secondary.armasec.dev", audience="https://this.api")
