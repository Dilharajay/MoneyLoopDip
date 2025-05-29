import factory
from decimal import Decimal
from core.models import Customer, Group, Contribution
from django.contrib.auth.hashers import make_password


class CustomerFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Customer

    username = factory.Sequence(lambda n: f'user{n}')
    email = factory.Sequence(lambda n: f'user{n}@example.com')
    password = make_password('password')
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    nic = factory.Sequence(lambda n: f'{n:09d}V')
    role = 'U'


class GroupFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Group

    group_name = factory.Sequence(lambda n: f'Group {n}')
    created_by = factory.SubFactory(CustomerFactory)
    size = 5
    amount = Decimal('100.00')
    cycle_duration = 6

    @factory.post_generation
    def members(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for member in extracted:
                self.members.add(member)


class ContributionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Contribution

    group = factory.SubFactory(GroupFactory)
    user = factory.SubFactory(CustomerFactory)
    amount = factory.LazyAttribute(lambda o: o.group.amount)