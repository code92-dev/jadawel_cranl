# e2e-tests/fixtures/licence.ts

- License · type · L5-L9 — type License = { id?: number, license: string, alreadyExistedAtStart:boolean }
- createLicense · function · L24-L47 — async function createLicense(key: string, user?: User): Promise<any>
- deleteLicense · function · L49-L58 — async function deleteLicense(license: License, user?: User): Promise<any>
