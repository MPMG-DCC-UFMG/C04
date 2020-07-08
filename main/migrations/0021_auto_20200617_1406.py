# Generated by Django 2.2.12 on 2020-06-17 14:06

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0020_crawlerinstance'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='crawlerinstance',
            name='id',
        ),
        migrations.AlterField(
            model_name='crawlerinstance',
            name='crawler_id',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, primary_key=True, serialize=False, to='main.CrawlRequest'),
        ),
    ]