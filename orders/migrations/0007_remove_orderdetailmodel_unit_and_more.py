# Generated by Django 5.0.6 on 2024-06-27 16:55

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("orders", "0006_ordersmodel_finish_num_ordersmodel_product_num"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="orderdetailmodel",
            name="unit",
        ),
        migrations.AlterField(
            model_name="orderdetailmodel",
            name="description",
            field=models.TextField(verbose_name="商品规格"),
        ),
    ]
