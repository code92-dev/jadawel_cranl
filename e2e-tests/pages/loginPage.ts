import { expect, Locator } from "@playwright/test";
import { JadawelPage, PageConfig } from "./jadawelPage";

export class LoginPage extends JadawelPage {
  readonly pageUrl = `login`;
  readonly emailInput: Locator;
  readonly passwordInput: Locator;
  readonly loginButton: Locator;
  readonly errorAlert: Locator;
  readonly languagePicker: Locator;

  constructor(pageConfig: PageConfig) {
    super(pageConfig);
    this.emailInput = this.page.locator('input[type="email"]').first();
    this.passwordInput = this.page.locator('input[type="password"]').first();
    // The label of the submit button is translated, so match on the form
    // instead of its text: these tests also run against the Arabic UI.
    this.loginButton = this.page.locator("form button").first();
    this.errorAlert = this.page.locator(".alert--error");
    this.languagePicker = this.page.locator(".lang-picker");
  }

  async fillCredentials(email: string, password: string) {
    await this.emailInput.fill(email);
    await this.passwordInput.fill(password);
  }

  async submit() {
    await this.loginButton.click();
  }

  /**
   * Signs in and waits until the app has landed on the first screen an
   * authenticated user sees: their workspace, or the dashboard when they do
   * not have one yet.
   */
  async loginWithPassword(email: string, password: string) {
    await this.fillCredentials(email, password);
    await this.submit();
    // Signing in lands on the workspaces homepage (`/dashboard` redirects there).
    await this.page.waitForURL(/\/(all-workspaces|workspace\/\d+|dashboard)/);
  }

  async loginExpectingFailure(email: string, password: string) {
    await this.fillCredentials(email, password);
    await this.submit();
    await this.errorAlert.waitFor();
  }

  async selectLanguage(name: string) {
    await this.languagePicker.click();
    await this.languagePicker.locator(".select__item").getByText(name).click();
  }

  async expectOnLoginPage() {
    await expect(this.page).toHaveURL(/\/login/);
  }
}
