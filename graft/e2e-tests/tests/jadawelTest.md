# e2e-tests/tests/jadawelTest.ts

- JadawelFixtures · type · L14-L18 — type JadawelFixtures = { workspacePage: WorkspacePage; builderPagePage: BuilderPagePage; automationWorkflowPage: AutomationWorkflowPage; };
- ExpectedHttpError · type · L20-L23 — type ExpectedHttpError = { status: number; urlIncludes: string; };
- JadawelOptions · type · L25-L27 — type JadawelOptions = { expectedHttpErrors: ExpectedHttpError[]; };
- monitorBrowserErrors · function · L29-L88 — function monitorBrowserErrors( page, expectedHttpErrors: ExpectedHttpError[] = [] )
- onConsole · function · L36-L62 — onConsole = (message)
- onPageError · function · L63-L65 — onPageError = (error)
- onResponse · function · L66-L70 — onResponse = (response)
