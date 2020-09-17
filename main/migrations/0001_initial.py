# Generated by Django 3.0.7 on 2020-09-14 12:58

import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='CrawlRequest',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('creation_date', models.DateTimeField()),
                ('last_modified', models.DateTimeField()),
                ('source_name', models.CharField(max_length=200)),
                ('base_url', models.CharField(max_length=200)),
                ('obey_robots', models.BooleanField(blank=True, null=True)),
                ('data', models.CharField(blank=True, max_length=2000, null=True, validators=[django.core.validators.RegexValidator('^[0-9a-zA-Z\\/\\\\-_]*$', 'This is not a valid path.')])),
                ('antiblock_download_delay', models.IntegerField(blank=True, null=True)),
                ('antiblock_autothrottle_enabled', models.BooleanField(blank=True, null=True)),
                ('antiblock_autothrottle_start_delay', models.IntegerField(blank=True, null=True)),
                ('antiblock_autothrottle_max_delay', models.IntegerField(blank=True, null=True)),
                ('antiblock_mask_type', models.CharField(blank=True, choices=[('none', 'None'), ('ip', 'IP rotation'), ('user_agent', 'User-agent rotation'), ('cookies', 'Use cookies')], default='none', max_length=15, null=True)),
                ('antiblock_ip_rotation_type', models.CharField(blank=True, choices=[('tor', 'Tor'), ('proxy', 'Proxy')], max_length=15, null=True)),
                ('antiblock_proxy_list', models.CharField(blank=True, max_length=2000, null=True)),
                ('antiblock_max_reqs_per_ip', models.IntegerField(blank=True, null=True)),
                ('antiblock_max_reuse_rounds', models.IntegerField(blank=True, null=True)),
                ('antiblock_reqs_per_user_agent', models.IntegerField(blank=True, null=True)),
                ('antiblock_user_agents_file', models.CharField(blank=True, max_length=2000, null=True)),
                ('antiblock_cookies_file', models.CharField(blank=True, max_length=2000, null=True)),
                ('antiblock_persist_cookies', models.BooleanField(blank=True, null=True)),
                ('captcha', models.CharField(choices=[('none', 'None'), ('image', 'Image'), ('sound', 'Sound')], default='none', max_length=15)),
                ('has_webdriver', models.BooleanField(blank=True, null=True)),
                ('webdriver_path', models.CharField(blank=True, max_length=1000, null=True)),
                ('img_xpath', models.CharField(blank=True, max_length=100, null=True)),
                ('sound_xpath', models.CharField(blank=True, max_length=100, null=True)),
                ('crawler_type', models.CharField(choices=[('static_page', 'Static Page'), ('form_page', 'Page with Form'), ('single_file', 'Single File'), ('bundle_file', 'Bundle File')], default='static_page', max_length=15)),
                ('explore_links', models.BooleanField(blank=True, null=True)),
                ('link_extractor_max_depth', models.IntegerField(blank=True, null=True)),
                ('link_extractor_allow', models.CharField(blank=True, max_length=1000, null=True)),
                ('link_extractor_allow_extensions', models.CharField(blank=True, max_length=2000, null=True)),
                ('templated_url_type', models.CharField(choices=[('none', 'None'), ('get', 'GET'), ('post', 'POST')], default='none', max_length=15)),
                ('formatable_url', models.CharField(blank=True, max_length=200, null=True)),
                ('param', models.CharField(blank=True, max_length=200, null=True)),
                ('post_dictionary', models.CharField(blank=True, max_length=1000, null=True)),
                ('http_status_response', models.CharField(blank=True, max_length=15, null=True)),
                ('invert_http_status', models.BooleanField(blank=True, null=True)),
                ('text_match_response', models.CharField(blank=True, max_length=2000, null=True)),
                ('invert_text_match', models.BooleanField(blank=True, null=True)),
                ('save_csv', models.BooleanField(blank=True, null=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='CrawlerInstance',
            fields=[
                ('creation_date', models.DateTimeField()),
                ('last_modified', models.DateTimeField()),
                ('instance_id', models.BigIntegerField(primary_key=True, serialize=False)),
                ('running', models.BooleanField()),
                ('crawler_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='instances', to='main.CrawlRequest')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
