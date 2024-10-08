# Generated by Django 5.0.2 on 2024-03-12 14:27

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('main', '0003_log_new_store_log_old_store'),
    ]

    operations = [
        migrations.AlterField(
            model_name='router',
            name='status',
            field=models.CharField(
                choices=[('in_stock', 'In stock'), ('new_sale', 'New sale'), ('collected', 'Collected'),
                         ('return', 'Return'), ('swap', 'Device swap'),
                         ('Internal use', 'Out of stock (Internal use)')], default='in_stock', max_length=50),
        ),
    ]
