import pytest
from model_bakery import baker

@pytest.fixture
def user_factory():
    def factory(**kwargs):
        return baker.make('core.Customer', **kwargs)
    return factory

@pytest.fixture
def group_factory():
    def factory(**kwargs):
        return baker.make('core.Group', **kwargs)
    return factory