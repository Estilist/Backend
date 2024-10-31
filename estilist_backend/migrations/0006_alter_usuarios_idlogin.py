# Generated by Django 5.1.2 on 2024-10-30 23:46

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('estilist_backend', '0005_usuarios_username'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterField(
            model_name='usuarios',
            name='idlogin',
            field=models.ForeignKey(blank=True, db_column='id', null=True, on_delete=django.db.models.deletion.DO_NOTHING, to=settings.AUTH_USER_MODEL),
        ),
    ]
