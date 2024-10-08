# Generated by Django 5.0.2 on 2024-03-12 12:20

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('main', '0002_alter_log_action'),
    ]

    operations = [
        migrations.AddField(
            model_name='log',
            name='new_store',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='new_store',
                                    to='main.store'),
        ),
        migrations.AddField(
            model_name='log',
            name='old_store',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='old_store',
                                    to='main.store'),
        ),
    ]
