# e2e-tests/fixtures/user.ts

- User · type · L4-L11 — type User = { name: string; email: string; password?: string; language: string; accessToken: string; refreshToken: string; };
- getTokenAuth · function · L13-L31 — async function getTokenAuth( email: String, password: String, ): Promise<User>
- getStaffUser · function · L33-L39 — async function getStaffUser(): Promise<User>
- createUser · function · L41-L70 — async function createUser( skipOnboarding = true, skipGuidedTours = true, ): Promise<User>
- deleteUser · function · L72-L74 — async function deleteUser(user: User): Promise<any>
