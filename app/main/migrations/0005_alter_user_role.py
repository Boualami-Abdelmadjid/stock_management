# Generated by Django 5.0.2 on 2024-03-13 07:47

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('main', '0004_alter_router_status'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='role',
            field=models.CharField(blank=True, choices=[('store_manager', 'Store manager'),
                                                        ('senior_management', 'Senior management'),
                                                        ('store_assistant', 'Store Assistant')], max_length=150,
                                   null=True),
        ),
    ]
