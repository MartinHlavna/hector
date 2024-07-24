import pytest

from src.backend.service import Service


@pytest.fixture(scope='session')
def setup_teardown(request):
    """
    Fixture to set up and tear down test context.
    Yields control back to the test function and performs cleanup after the test function is done.
    """
    # Initialization code, if needed
    nlp = Service.initialize_nlp()
    dictionaries = Service.initialize_dictionaries(github_token=request.config.option.github_token)
    spellcheck_dictionary = dictionaries["spellcheck"]
    thesaurus = dictionaries["thesaurus"]
    yield nlp, spellcheck_dictionary, thesaurus
    # Cleanup code, if needed


def pytest_addoption(parser):
    parser.addoption("--github_token", action="store", default=None)
