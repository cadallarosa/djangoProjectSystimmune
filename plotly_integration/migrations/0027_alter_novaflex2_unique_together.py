# Generated by Django 5.1.4 on 2025-03-18 18:44

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('plotly_integration', '0026_alter_novaflex2_gln_alter_novaflex2_glu_and_more'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='novaflex2',
            unique_together={('date_time', 'sample_id')},
        ),
    ]
