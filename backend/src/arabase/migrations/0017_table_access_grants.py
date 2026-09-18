# Table-scoped guest access (docs/TABLE_LEVEL_ACCESS_PLAN.md).
#
# Only the two new models are here. `makemigrations arabase` also reports a
# pre-existing drift on `safe_reason_code` from the MCP protection models; it
# predates this branch and is left for whoever owns that change.

import django.db.models.deletion
import jadawel.core.fields
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('arabase', '0016_kanban_view'),
        ('core', '0117_jadawel_rename_show_help_request'),
        ('database', '0213_viewgroupby_viewsort_priority'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='PendingTableGrant',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('level', models.CharField(choices=[('VIEWER', 'Viewer'), ('EDITOR', 'Editor')], default='VIEWER', max_length=16)),
                ('invitation', models.ForeignKey(help_text='The core invitation that will materialise this grant.', on_delete=django.db.models.deletion.CASCADE, related_name='pending_table_grants', to='core.workspaceinvitation')),
                ('table', models.ForeignKey(help_text='The table the invited person will be allowed to reach.', on_delete=django.db.models.deletion.CASCADE, related_name='pending_guest_grants', to='database.table')),
            ],
            options={
                'ordering': ('id',),
                'unique_together': {('invitation', 'table')},
            },
        ),
        migrations.CreateModel(
            name='TableGrant',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('updated_on', jadawel.core.fields.SyncedDateTimeField(auto_now=True)),
                ('level', models.CharField(choices=[('VIEWER', 'Viewer'), ('EDITOR', 'Editor')], default='VIEWER', help_text='Whether the member may only read the table or also edit its rows.', max_length=16)),
                ('granted_by', models.ForeignKey(help_text='The admin who granted the access. Kept for the audit trail.', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('table', models.ForeignKey(help_text='The table the member is allowed to reach.', on_delete=django.db.models.deletion.CASCADE, related_name='guest_grants', to='database.table')),
                ('workspace_user', models.ForeignKey(help_text='The workspace membership this grant widens.', on_delete=django.db.models.deletion.CASCADE, related_name='table_grants', to='core.workspaceuser')),
            ],
            options={
                'ordering': ('id',),
                'unique_together': {('workspace_user', 'table')},
            },
        ),
    ]
