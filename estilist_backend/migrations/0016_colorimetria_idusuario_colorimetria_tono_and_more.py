# Generated by Django 5.1.2 on 2024-11-11 21:41

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('estilist_backend', '0015_alter_colorimetria_options_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='colorimetria',
            name='tono',
            field=models.CharField(blank=True, db_column='Tono', db_comment='Frio, Calido, Neutro', max_length=50, null=True),
        ),
    
    ]
