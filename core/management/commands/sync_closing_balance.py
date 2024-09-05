from datetime import datetime

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from account.models import User
from core.models import PaymentMode
from core.signals import update_closing_balance


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('--email', type=str, required=True)
        parser.add_argument('--month', type=int, required=True)
        parser.add_argument('--year', type=int, required=True)

    def handle(self, *args, **options):
        email = options['email']
        month = options['month']
        year = options['year']
        year_limit = datetime.today().year + 5

        if 1 < month > 12:
            raise CommandError('Month must be between 1 and 12')

        if 1980 < year > year_limit:
            raise CommandError(f'Year must be between 1980 and {year_limit}')

        user = User.objects.filter(email=email).first()

        if not user:
            raise CommandError('User does not exist')

        with transaction.atomic():
            [
                update_closing_balance(user, month, year, mode)
                for mode in PaymentMode.objects.filter(is_active=True)
            ]
