from datetime import datetime

from dateutil import rrule
from django.db.models.signals import post_save
from django.dispatch import receiver

from core.models import PaymentTransaction, MonthlyBalance


@receiver(post_save, sender=PaymentTransaction, dispatch_uid=None)
def update_balance(sender, instance, **kwargs):
    mode = instance.payment_mode
    year = instance.date.year
    month = instance.date.month
    user = instance.user

    update_closing_balance(user, month, year, mode)


def update_closing_balance(user, month, year, mode):
    start_date = datetime(day=1, month=month, year=year)
    end_date = datetime.now()

    for dt in rrule.rrule(rrule.MONTHLY, dtstart=start_date, until=end_date):
        month = dt.month
        year = dt.year
        month_expense = PaymentTransaction.get_sum(user, month, year, mode)
        month_ob = MonthlyBalance.get_ob(user, month, year, mode)
        cb = month_ob + month_expense

        MonthlyBalance.objects.update_or_create(
            month=month,
            year=year,
            payment_mode=mode,
            user=user,
            defaults={'cb': cb},
            create_defaults={'cb': cb},
        )
