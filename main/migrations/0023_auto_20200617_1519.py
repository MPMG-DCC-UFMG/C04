# Generated by Django 2.2.12 on 2020-06-17 15:19

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0022_remove_crawlerinstance_started_at'),
    ]

    operations = [
        migrations.AlterField(
            model_name='crawlerinstance',
            name='crawler_id',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, primary_key=True, serialize=False, to='main.CrawlRequest', unique=True),
        ),
    ]
