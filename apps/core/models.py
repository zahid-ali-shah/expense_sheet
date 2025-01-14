import datetime
import uuid

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Sum, Q, Value, DecimalField
from django.db.models.functions import Coalesce
from django.utils.translation import gettext_lazy as _
from model_utils.models import TimeStampedModel


class Category(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name


class Item(TimeStampedModel):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    is_deprecated = models.BooleanField(default=False)
    is_highlighted = models.BooleanField(default=False, help_text="Highlight this item in monthly summary")
    categories = models.ManyToManyField(Category, related_name='items', blank=True)

    def __str__(self):
        return self.name

    @staticmethod
    def get_monthly_aggregate_for_highlighted_items(user, month, year):
        """Get monthly aggregate for items marked as highlighted, including those with zero total sum."""
        highlighted_items = (
            Item.objects.filter(is_highlighted=True)
            .annotate(
                total=Coalesce(
                    Sum(
                        'daily_expenses__transaction__amount',
                        filter=Q(daily_expenses__transaction__user=user) &
                               Q(daily_expenses__transaction__date__month=month) &
                               Q(daily_expenses__transaction__date__year=year)
                    ),
                    Value(0),
                    output_field=DecimalField()
                )
            )
            .values('name', 'total')
        )
        return highlighted_items

    @classmethod
    def get_monthly_aggregate_by_category(cls, user, month, year):
        """Get monthly aggregate for all items grouped by category, including those with zero total sum."""
        category_aggregates = (
            Category.objects
            .annotate(
                total=Coalesce(
                    Sum(
                        'items__daily_expenses__transaction__amount',
                        filter=Q(items__daily_expenses__transaction__user=user) &
                               Q(items__daily_expenses__transaction__date__month=month) &
                               Q(items__daily_expenses__transaction__date__year=year)
                    ),
                    Value(0),
                    output_field=DecimalField()
                )
            )
            .values('name', 'total')
            .order_by('name')
        )
        return category_aggregates


class DailyExpense(TimeStampedModel):
    item = models.ForeignKey(
        Item, on_delete=models.CASCADE, related_name='daily_expenses', help_text="Item of daily expense"
    )
    transaction = models.OneToOneField('PaymentTransaction', on_delete=models.RESTRICT)
    is_loan = models.BooleanField(default=False, help_text="Whether this expense is a loan")
    trip = models.ForeignKey('Trip', on_delete=models.RESTRICT, null=True, blank=True)

    @staticmethod
    def get_all_expenses(user, month, year):
        return DailyExpense.objects.filter(
            transaction__user=user, transaction__date__month=month, transaction__date__year=year,
        ).select_related(
            'item', 'transaction', 'transaction__payment_mode', 'transaction__user',
        ).all().order_by('transaction__date', 'transaction__payment_mode__type')

    @staticmethod
    def get_sum_of_expenses_by_mode(user, month, year, mode):
        return DailyExpense.objects.filter(
            transaction__user=user, transaction__date__month=month, transaction__date__year=year,
            transaction__payment_mode__id=mode,
        ).select_related('transaction__user', 'item', 'transaction', 'transaction__payment_mode').aggregate(
            Sum('transaction__amount', default=0)
        )['transaction__amount__sum']

    @staticmethod
    def get_sum_of_expenses(user, month, year):
        return DailyExpense.objects.filter(
            transaction__user=user, transaction__date__month=month, transaction__date__year=year,
        ).select_related('transaction__user', 'item', 'transaction', 'transaction__payment_mode').aggregate(
            Sum('transaction__amount', default=0)
        )['transaction__amount__sum']

    def __str__(self):
        return f'{self.item}'


class TypeOfPaymentModes(models.TextChoices):
    CASH = "CA", _("Cash")
    CREDIT = "CR", _("Credit Card")
    BANK = "BN", _("Bank transaction")


class CurrencyChoices(models.TextChoices):
    USD = "USD", _("US Dollar")
    PKR = "PKR", _("Pakistani Rupee")
    EUR = "EUR", _("Euro")
    GBP = "GBP", _("British Pound")


class PaymentMode(TimeStampedModel):
    name = models.CharField(max_length=100, unique=True)
    type = models.CharField(max_length=2, choices=TypeOfPaymentModes, default=TypeOfPaymentModes.CASH)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    is_active = models.BooleanField(default=True)
    bg_color = models.CharField(max_length=6, default='175175')
    currency = models.CharField(max_length=3, choices=CurrencyChoices.choices, default=CurrencyChoices.PKR)
    conversion_rate = models.DecimalField(max_digits=10, decimal_places=4, default=1.0000)

    def __str__(self):
        return f'{self.name}'


class PaymentTransaction(TimeStampedModel):
    payment_mode = models.ForeignKey(PaymentMode, on_delete=models.RESTRICT, related_name='transactions')
    date = models.DateField(default=datetime.date.today)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='payment_transactions'
    )
    is_deposited = models.BooleanField(default=False)
    comment = models.TextField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.is_deposited:
            self.amount = -self.amount
        super().save(*args, **kwargs)

    @staticmethod
    def get_all(user, month, year, mode):
        return PaymentTransaction.objects.filter(
            user=user, date__month=month, date__year=year, payment_mode=mode
        ).select_related(
            'user', 'payment_mode'
        ).all().order_by('date', 'created')

    @staticmethod
    def get_all_name(user, month, year, mode):
        return PaymentTransaction.objects.filter(
            user=user, date__month=month, date__year=year, payment_mode=mode
        ).select_related(
            'user', 'payment_mode'
        ).all().order_by('date', 'created')

    @staticmethod
    def get_sum(user, month, year, mode):
        return PaymentTransaction.get_all(user, month, year, mode).aggregate(
            Sum('amount', default=0)
        )['amount__sum']

    @staticmethod
    def get_queryset_sum(transactions):
        return transactions.aggregate(
            Sum('amount', default=0)
        )['amount__sum']

    def __str__(self):
        return f'{self.id} - {self.amount}'


class MonthlyBalance(TimeStampedModel):
    month = models.PositiveSmallIntegerField(
        validators=[
            MaxValueValidator(12),
            MinValueValidator(1)
        ]
    )
    year = models.PositiveSmallIntegerField(
        validators=[
            MaxValueValidator(2050),
            MinValueValidator(2000)
        ]
    )
    cb = models.DecimalField(max_digits=10, decimal_places=2)
    payment_mode = models.ForeignKey(
        PaymentMode, on_delete=models.RESTRICT, related_name='ob'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='ob_user'
    )

    class Meta:
        unique_together = (('month', 'year', 'payment_mode', 'user',),)

    @staticmethod
    def get_ob(user, month, year, mode):
        from apps.core.helpers import get_pre_month

        month, year = get_pre_month(month, year)
        return MonthlyBalance.get_cb(user, month, year, mode)

    @staticmethod
    def get_cb(user, month, year, mode):
        ob_object = MonthlyBalance.objects.filter(
            user=user, month=month, year=year, payment_mode=mode
        ).first()
        return ob_object.cb if ob_object else 0


class Trip(TimeStampedModel):
    location = models.CharField(max_length=100)
    description = models.TextField(null=True, blank=True)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    distance = models.PositiveSmallIntegerField(null=True, blank=True, verbose_name='Distance (KM)')

    @property
    def cost(self):
        return abs(self.dailyexpense_set.aggregate(total_cost=Sum('transaction__amount'))['total_cost'] or 0)

    def __str__(self):
        return f'{self.id} - {self.location}'
