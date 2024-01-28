# Generated by Django 5.0.1 on 2024-01-25 17:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0011_category_alerted'),
    ]

    operations = [
        migrations.AddField(
            model_name='router',
            name='reason',
            field=models.CharField(blank=True, max_length=150, null=True),
        ),
        migrations.AddField(
            model_name='router',
            name='status',
            field=models.CharField(choices=[('in_stock', 'In stock'), ('new_sale', 'New sale'), ('collected', 'Collected'), ('return', 'Return'), ('swap', 'Device swap')], default='in_stock', max_length=50),
        ),
    ]
