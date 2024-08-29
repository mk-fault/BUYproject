# Generated by Django 4.2.4 on 2024-08-29 21:03

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("orders", "0013_remove_orderdetailmodel_image_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="orderdetailmodel",
            name="image",
            field=models.CharField(
                blank=True, max_length=200, null=True, verbose_name="商品图片"
            ),
        ),
        migrations.AddField(
            model_name="orderdetailmodel",
            name="license",
            field=models.CharField(
                blank=True, max_length=200, null=True, verbose_name="商品资质"
            ),
        ),
    ]
