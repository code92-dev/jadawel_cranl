# web-frontend/test/fixtures/user.js

- aUser · function · L1-L27 — function aUser({ id = 1, username = 'user@jadawl.site', name = 'user_name', workspaces = [ { id: 1, name: 'some_workspace', permissions: 'ADMIN', }, ], lastLogin = '2021-04-26T07:50:45.643059Z', dateJoined = '2021-04-21T12:04:27.379781Z', isActive = true, isStaff = true, })
- createUsersForAdmin · function · L29-L46 — function createUsersForAdmin( mock, users, page, { count = null, search = null, sorts = null } )
- expectUserDeleted · function · L48-L50 — function expectUserDeleted(mock, userId)
- expectUserUpdated · function · L52-L56 — function expectUserUpdated(mock, user, changes)
- expectUserUpdatedRespondsWithError · function · L58-L60 — function expectUserUpdatedRespondsWithError(mock, user, error)
