# web-frontend/modules/core/services/userSource.js

- fetchAll · method · L3-L5 — fetchAll(applicationId)
- fetchUserRoles · method · L6-L8 — fetchUserRoles(applicationId)
- create · method · L9-L20 — create(applicationId, userSourceType, values, beforeId = null)
- update · method · L21-L23 — update(userSourceId, values)
- delete · method · L24-L26 — delete(userSourceId)
- move · method · L27-L31 — move(userSourceId, beforeId)
- getUserSourceUsers · method · L32-L42 — getUserSourceUsers(applicationId, search = '')
- forceAuthenticate · method · L43-L47 — forceAuthenticate(userSourceId, userId)
- authenticate · method · L48-L50 — authenticate(userSourceId, credentials)
- refreshAuth · method · L51-L59 — refreshAuth(refreshToken)
- blacklistToken · method · L60-L69 — blacklistToken(refreshToken)
