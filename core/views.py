import calendar
import datetime
import logging

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.shortcuts import render
from django.urls import reverse
from django.views import View

from core.helpers import get_expense_icon, get_pre_month, get_next_month
from core.models import (
    DailyExpense,
    TypeOfPaymentModes,
    PaymentTransaction,
    PaymentMode,
    MonthlyBalance
)

logger = logging.getLogger(__name__)


class HomeView(LoginRequiredMixin, View):

    def get(self, request):
        now = datetime.datetime.now()
        try:
            year = int(request.GET.get('year', now.year))
            month = int(request.GET.get('month', now.month))
        except ValueError as vex:
            logger.error(f'Invalid year or month entered. Exception={vex}')
            return HttpResponse(status=400)

        expenses = {}
        db_expenses = DailyExpense.get_all_expenses(request.user, month, year)
        total_expense = 0
        total_credit_expenses = 0
        no_of_days_in_current_month = calendar.monthrange(year, month)[1]
        month_dates = [datetime.date(year, month, day) for day in range(1, no_of_days_in_current_month + 1)]

        for expense in db_expenses:
            payment_mode = expense.transaction.payment_mode
            amount = expense.transaction.amount
            expense.transaction.amount = abs(amount)
            total_expense = amount + total_expense
            date = expense.transaction.date
            expense.icon = get_expense_icon(payment_mode.type)
            day = expenses.get(date, [])
            day.append(expense)
            expenses[date] = day

            if payment_mode.type == TypeOfPaymentModes.CREDIT:
                total_credit_expenses = amount + total_credit_expenses

        for day_date in month_dates:
            if expenses.get(day_date, None):
                continue
            expenses[day_date] = []

        previous_month, new_year = get_pre_month(month, year)
        _, _, total, mode_dict = get_mode_current_status(request, True)

        return render(request, 'home.html', {
            'month': calendar.month_name[month],
            'year': year,
            'expenses': dict(sorted(expenses.items())),
            'total_expense': total_expense,
            'total_credit_expenses': total_credit_expenses,
            'opening_balance': DailyExpense.get_sum_of_expenses(request.user, previous_month, new_year),
            'mode_dict': mode_dict,
            'total': total
        })


class BankView(LoginRequiredMixin, View):

    def get(self, request):
        year, month, _, mode_dict = get_mode_current_status(request, False)
        m_previous = get_pre_month(month, year)
        m_next = get_next_month(month, year)
        return render(request, 'core/bank.html', {
            'month': calendar.month_name[month],
            'year': year,
            'mode_dict': mode_dict,
            'next': f"{reverse('bank')}?month={m_next[0]}&year={m_next[1]}",
            'previous': f"{reverse('bank')}?month={m_previous[0]}&year={m_previous[1]}",
        })


def get_mode_current_status(request, short):
    now = datetime.datetime.now()
    mode_dict = {}
    total = 0

    try:
        year = int(request.GET.get('year', now.year))
        month = int(request.GET.get('month', now.month))
    except ValueError as vex:
        logger.error(f'Invalid year or month entered. Exception={vex}')
        return HttpResponse(status=400)

    for mode in PaymentMode.objects.filter(is_active=True).all().order_by('name'):
        transactions = PaymentTransaction.get_all_name(request.user, month, year, mode)
        ob = MonthlyBalance.get_ob(request.user, month, year, mode)
        sum_total = PaymentTransaction.get_queryset_sum(transactions)
        mode_dict[mode.name] = {
            'transactions': transactions,
            'bg_color': mode.bg_color,
            'sum': sum_total,
            'ob': ob,
            'cb': sum_total + ob
        }
        mode_dict_val = mode_dict[mode.name]
        total = mode_dict_val['cb'] + total

        if not short:
            mode_dict_val['transactions'] = transactions
            mode_dict_val['ob'] = ob
            mode_dict[mode.name] = mode_dict_val

    return year, month, total, mode_dict
