# Generated by Django 5.1 on 2024-09-02 16:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0014_orderdetailmodel_image_orderdetailmodel_license'),
    ]

    operations = [
        migrations.AddField(
            model_name='ordersmodel',
            name='note',
            field=models.TextField(blank=True, null=True, verbose_name='备注'),
        ),
    ]
