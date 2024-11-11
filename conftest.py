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
    dictionaries = Service.initialize_dictionaries(github_token=request.config.option.github_token,
                                                   github_user=request.config.option.github_user)
    spellcheck_dictionary = dictionaries["spellcheck"]
    thesaurus = dictionaries["thesaurus"]
    yield nlp, spellcheck_dictionary, thesaurus, request.config.option.github_token, request.config.option.github_user
    # Cleanup code, if needed


def pytest_addoption(parser):
    parser.addoption("--github_token", action="store", default=None)
    parser.addoption("--github_user", action="store", default=None)
