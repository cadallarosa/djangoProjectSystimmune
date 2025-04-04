# Generated by Django 5.1.4 on 2025-03-03 17:52

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('plotly_integration', '0004_alter_projectinformation_protein'),
    ]

    operations = [
        migrations.CreateModel(
            name='EmpowerColumnLogbook',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('column_serial_number', models.CharField(max_length=255, unique=True)),
                ('column_name', models.CharField(max_length=255)),
                ('total_injections', models.IntegerField(default=0)),
                ('most_recent_injection_date', models.DateField(blank=True, null=True)),
            ],
            options={
                'db_table': 'empower_column_logbook',
                'managed': True,
            },
        ),
        migrations.AlterField(
            model_name='report',
            name='project_id',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='chrommetadata',
            name='average_pressure',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='chrommetadata',
            name='max_pressure',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='chrommetadata',
            name='min_pressure',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='chrommetadata',
            name='peak_pressure_time',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='chrommetadata',
            name='pressure_stddev',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='chrommetadata',
            name='pressure_variance',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='chrommetadata',
            name='retention_time_range',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='samplemetadata',
            name='column_id',
            field=models.ForeignKey(db_column='column_id', null=True, on_delete=django.db.models.deletion.SET_NULL, to='plotly_integration.empowercolumnlogbook'),
        ),
        migrations.DeleteModel(
            name='ProjectID',
        ),
    ]
