# backend/tests/jadawel/contrib/database/test_database_plugin.py

- test_user_created_without_workspace_returns · function · L8-L15 — def test_user_created_without_workspace_returns(data_fixture): # If the user registered without being invited, and the Setting # `allow_global_workspace_creation` is set to `False`, then no `Workspace` will # be created for this `user`.
- test_user_created_with_invitation_or_template_returns · function · L19-L33 — def test_user_created_with_invitation_or_template_returns(data_fixture): # If the user created an account in combination with a workspace invitation we # don't want to create the initial data in the workspace because data should # already exist.
