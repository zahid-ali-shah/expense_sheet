from django.contrib import admin
from django.utils.html import format_html

from core.forms import DailyExpenseForm, PaymentTransactionForm
from core.models import (
    Item,
    DailyExpense,
    PaymentMode,
    TypeOfPaymentModes,
    PaymentTransaction,
    MonthlyBalance,
    Trip,
)
from utils.admin import ReadOnlyAdminInlineMixin


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'description', 'is_deprecated')
    search_fields = ('id', 'name')
    list_filter = ('is_deprecated',)


@admin.register(DailyExpense)
class DailyExpenseAdmin(admin.ModelAdmin):
    form = DailyExpenseForm
    list_display = ('id', 'item', 'expense', 'transaction', 'payment_through', 'comment', 'date', 'trip', )
    readonly_fields = ('transaction',)
    list_display_links = ('id', 'transaction')
    search_fields = ('id', 'item')
    list_filter = ('transaction__payment_mode',)
    list_select_related = ('item', 'transaction', 'transaction__payment_mode')
    autocomplete_fields = ['item']
    fieldsets = [
        (
            'Daily Expense', {'fields': ('item', 'transaction', 'is_loan', 'trip')},
        ),
        (
            'Transaction', {
                'fields': ('user', 'date', 'amount', 'is_deposited', 'payment_mode', 'comment')
            },
        )
    ]
    admin_order_field = 'transaction__date'

    def get_queryset(self, request):
        qs = super(DailyExpenseAdmin, self).get_queryset(request)
        return qs.order_by('-transaction__date')

    def comment(self, obj):
        return obj.transaction.comment

    def payment_through(self, obj):
        return obj.transaction.payment_mode

    def date(self, obj):
        return obj.transaction.date

    def expense(self, obj):
        return format_html(
            '<span style="color: #{};">{}</span>',
            ('008000' if obj.transaction.is_deposited else 'FF0000'), abs(obj.transaction.amount)
        )

    def get_form(self, request, obj=None, **kwargs):
        form = super(DailyExpenseAdmin, self).get_form(request, obj, **kwargs)
        form.base_fields['user'].initial = request.user
        return form

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'item':
            kwargs["queryset"] = Item.objects.filter(is_deprecated=False)

        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(PaymentMode)
class PaymentModeAdmin(admin.ModelAdmin):
    list_display = ('id', 'uuid', 'name', 'type', 'is_active', 'bg_color_code')
    search_fields = ('name',)
    list_filter = ('type', 'is_active')

    def bg_color_code(self, obj):
        return format_html(
            '<span style="color: #{};">#{}</span>',
            obj.bg_color, obj.bg_color
        )


@admin.register(PaymentTransaction)
class PaymentTransactionAdmin(admin.ModelAdmin):
    form = PaymentTransactionForm
    list_display = ('id', 'user', 'colored_amount', 'is_deposited', 'payment_mode', 'date', 'comment',)
    list_filter = ('payment_mode',)
    list_select_related = ('user', 'payment_mode',)
    ordering = ['-date', ]

    @admin.display(description="amount")
    def colored_amount(self, obj):
        return format_html(
            '<span style="color: #{};">{}</span>',
            ('008000' if obj.is_deposited else 'FF0000'), abs(obj.amount)
        )

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'payment_mode':
            kwargs["queryset"] = PaymentMode.objects.filter(is_active=True)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def get_form(self, request, obj=None, **kwargs):
        form = super(PaymentTransactionAdmin, self).get_form(request, obj, **kwargs)
        form.base_fields['payment_mode'].initial = PaymentMode.objects.filter(
            type=TypeOfPaymentModes.CASH, is_active=True
        ).first()
        form.base_fields['user'].initial = request.user
        return form


@admin.register(MonthlyBalance)
class MonthlyBalanceAdmin(admin.ModelAdmin):
    list_display = ('id', 'month', 'year', 'cb', 'user',)


class DailyExpenseInlineAdmin(ReadOnlyAdminInlineMixin, admin.TabularInline):
    model = DailyExpense
    fields = ['item', 'transaction', 'date', ]
    readonly_fields = ('date', )

    def date(self, obj):
        return obj.transaction.date


@admin.register(Trip)
class TripAdmin(admin.ModelAdmin):
    list_display = ('id', 'location', 'start_date', 'end_date', 'description', 'distance', 'cost', )
    inlines = (DailyExpenseInlineAdmin,)
