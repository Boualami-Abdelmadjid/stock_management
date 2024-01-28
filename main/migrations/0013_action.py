# Generated by Django 5.0.1 on 2024-01-25 18:08

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0012_router_reason_router_status'),
    ]

    operations = [
        migrations.CreateModel(
            name='Action',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('action', models.CharField(choices=[('collect', 'Collect'), ('sale', 'Sale'), ('return', 'Return'), ('swap', 'Device swap')], max_length=50)),
                ('imei', models.CharField(max_length=150)),
                ('imei2', models.CharField(blank=True, max_length=150, null=True)),
                ('reason', models.CharField(blank=True, max_length=50, null=True)),
                ('comment', models.TextField(blank=True, null=True)),
                ('user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
