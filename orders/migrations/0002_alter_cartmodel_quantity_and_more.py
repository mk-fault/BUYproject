# Generated by Django 5.0.6 on 2024-06-13 17:30

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("orders", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="cartmodel",
            name="quantity",
            field=models.DecimalField(
                decimal_places=2, max_digits=10, verbose_name="购买数量"
            ),
        ),
        migrations.AlterField(
            model_name="orderdetailmodel",
            name="order_quantity",
            field=models.DecimalField(
                decimal_places=2, max_digits=10, verbose_name="购入数量"
            ),
        ),
        migrations.AlterField(
            model_name="orderdetailmodel",
            name="received_quantity",
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                max_digits=10,
                null=True,
                verbose_name="实收数量",
            ),
        ),
    ]
