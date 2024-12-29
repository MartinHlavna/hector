import pytest

from src.backend.service.import_service import ImportService
from src.backend.service.nlp_service import NlpService
from src.backend.service.spellcheck_service import SpellcheckService
from test_utils import TestUtils


@pytest.fixture(scope='session')
def setup_teardown(request):
    """
    Fixture to set up and tear down test context.
    Yields control back to the test function and performs cleanup after the test function is done.
    """
    # Initialization code, if needed
    nlp = NlpService.initialize()
    dictionaries = SpellcheckService.initialize(github_token=request.config.option.github_token,
                                                github_user=request.config.option.github_user)
    spellcheck_dictionary = dictionaries["spellcheck"]
    thesaurus = dictionaries["thesaurus"]
    ImportService.ensure_pandoc_available()
    yield nlp, spellcheck_dictionary, thesaurus, request.config.option.github_token, request.config.option.github_user
    # Cleanup code, if needed


def pytest_addoption(parser):
    parser.addoption("--github_token", action="store", default=None)
    parser.addoption("--github_user", action="store", default=None)


def pytest_configure(config):
    config.addinivalue_line(
        "markers", "disable_socket: Disable socket connections for this test."
    )


@pytest.fixture(autouse=True)
def disable_socket_fixture(request, monkeypatch):
    if 'disable_socket' in request.keywords:
        # Disable socket methods
        # Get the monkeypatch fixture
        TestUtils.disable_socket(monkeypatch)
