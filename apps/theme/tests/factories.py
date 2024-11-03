import factory
from django.contrib.auth import get_user_model
import uuid

User = get_user_model()
DEFAULT_PASSWORD = 'zahid'


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    email = factory.LazyAttribute(lambda _: f'user-{uuid.uuid4()}@example.com')  # Unique email generation
    first_name = factory.Faker('first_name')  # Generates a random first name
    last_name = factory.Faker('last_name')  # Generates a random last name
    password = factory.PostGenerationMethodCall('set_password', DEFAULT_PASSWORD)
