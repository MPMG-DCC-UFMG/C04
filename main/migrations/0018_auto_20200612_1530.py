# Generated by Django 2.2.12 on 2020-06-12 15:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0017_auto_20200612_1505'),
    ]

    operations = [
        migrations.AlterField(
            model_name='crawlrequest',
            name='link_extractor_allow',
            field=models.CharField(blank=True, max_length=1000, null=True),
        ),
    ]
