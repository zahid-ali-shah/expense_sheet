# Generated by Django 5.0.6 on 2024-11-03 21:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0010_paymentmode_conversion_rate_paymentmode_currency'),
    ]

    operations = [
        migrations.AddField(
            model_name='item',
            name='is_highlighted',
            field=models.BooleanField(default=False, help_text='Highlight this item in monthly summary'),
        ),
    ]