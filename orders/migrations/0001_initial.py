# Generated by Django 5.0.6 on 2024-06-13 14:04

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("goods", "0009_alter_pricemodel_status"),
    ]

    operations = [
        migrations.CreateModel(
            name="FundsModel",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=100, verbose_name="经费来源名字")),
            ],
            options={
                "verbose_name": "经费来源",
                "verbose_name_plural": "经费来源",
                "db_table": "funds",
            },
        ),
        migrations.CreateModel(
            name="OrdersModel",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("0", "未接单"),
                            ("1", "未发货"),
                            ("2", "配送中"),
                            ("3", "配送完成"),
                            ("4", "订单完成"),
                            ("-1", "撤销"),
                        ],
                        max_length=10,
                        verbose_name="订单状态",
                    ),
                ),
                ("creater_id", models.IntegerField(verbose_name="订单创建人ID")),
                (
                    "create_time",
                    models.DateTimeField(auto_now_add=True, verbose_name="订单创建时间"),
                ),
                (
                    "accepter_id",
                    models.IntegerField(blank=True, null=True, verbose_name="订单接受人ID"),
                ),
                (
                    "accept_time",
                    models.DateTimeField(blank=True, null=True, verbose_name="订单接受时间"),
                ),
                (
                    "finish_time",
                    models.DateTimeField(blank=True, null=True, verbose_name="订单完成时间"),
                ),
                (
                    "finish_status",
                    models.CharField(
                        choices=[("0", "未完成"), ("-1", "完成但数量有误"), ("1", "全部完成")],
                        max_length=10,
                        verbose_name="订单完成情况",
                    ),
                ),
            ],
            options={
                "verbose_name": "订单",
                "verbose_name_plural": "订单",
                "db_table": "orders",
            },
        ),
        migrations.CreateModel(
            name="CartModel",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("quantity", models.IntegerField(verbose_name="购买数量")),
                ("creater_id", models.IntegerField(verbose_name="加购人ID")),
                (
                    "product",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="goods.goodsmodel",
                        verbose_name="商品实例",
                    ),
                ),
                (
                    "funds",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="orders.fundsmodel",
                        verbose_name="经费实例",
                    ),
                ),
            ],
            options={
                "verbose_name": "购物车",
                "verbose_name_plural": "购物车",
                "db_table": "cart",
            },
        ),
        migrations.CreateModel(
            name="OrderDetailModel",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("product_id", models.IntegerField(verbose_name="商品ID")),
                ("product_name", models.CharField(max_length=100, verbose_name="商品名称")),
                ("product_des", models.TextField(verbose_name="商品描述")),
                ("unit", models.CharField(max_length=100, verbose_name="商品类别")),
                ("category", models.CharField(max_length=100, verbose_name="商品计量单位")),
                (
                    "price",
                    models.DecimalField(
                        decimal_places=2, max_digits=10, verbose_name="商品价格"
                    ),
                ),
                ("funds", models.CharField(max_length=100, verbose_name="经费来源")),
                ("order_quantity", models.IntegerField(verbose_name="购入数量")),
                (
                    "received_quantity",
                    models.IntegerField(blank=True, null=True, verbose_name="实收数量"),
                ),
                (
                    "cost",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        max_digits=10,
                        null=True,
                        verbose_name="商品总价",
                    ),
                ),
                (
                    "recipient_id",
                    models.IntegerField(blank=True, null=True, verbose_name="收货人ID"),
                ),
                (
                    "recipient_time",
                    models.DateTimeField(blank=True, null=True, verbose_name="收货时间"),
                ),
                (
                    "order",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="orders.ordersmodel",
                        verbose_name="订单实例",
                    ),
                ),
            ],
            options={
                "verbose_name": "订单详情",
                "verbose_name_plural": "订单详情",
                "db_table": "order_detail",
            },
        ),
    ]
