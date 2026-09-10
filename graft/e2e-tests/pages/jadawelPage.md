# e2e-tests/pages/jadawelPage.ts

- GotoFn · type · L7-L7 — type GotoFn = (url: string, options?: GotoOptions) => Promise<Response | null>;
- PageConfig · type · L9-L9 — type PageConfig = { page: Page; goto: GotoFn };
- JadawelPage · class · L11-L55 — class JadawelPage
- constructor · method · L17-L20 — constructor({ page, goto }: PageConfig)
- authenticate · method · L22-L24 — async authenticate(user: User)
- goto · method · L26-L31 — async goto(params = {})
- checkOnPage · method · L33-L35 — async checkOnPage()
- changeDropdown · method · L37-L50 — async changeDropdown( currentValue: string, newValue: string, location?: Locator, )
- getFullUrl · method · L52-L54 — getFullUrl()
