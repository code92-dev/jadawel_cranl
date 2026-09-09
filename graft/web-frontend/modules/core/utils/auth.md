# web-frontend/modules/core/utils/auth.js

- setToken · function · L12-L31 — setToken = ( appOrContext, token, key = cookieTokenName, configuration = { sameSite: null } )
- setUserSessionCookie · function · L47-L76 — setUserSessionCookie = ( appOrContext, signedUserSession, key = userSessionCookieName, configuration = { sameSite: null } )
- unsetToken · function · L78-L84 — unsetToken = (appOrContext, key = cookieTokenName)
- unsetUserSessionCookie · function · L86-L95 — unsetUserSessionCookie = ( appOrContext, key = userSessionCookieName )
- getToken · function · L97-L103 — getToken = async (appOrContext, key = cookieTokenName)
- getTokenIfEnoughTimeLeft · function · L105-L120 — getTokenIfEnoughTimeLeft = async ( appOrContext, key = cookieTokenName )
- logoutAndRedirectToLogin · function · L122-L146 — logoutAndRedirectToLogin = async ( router, store, showSessionExpiredToast = false, showPasswordChangedToast = false, invalidateToken = false )
