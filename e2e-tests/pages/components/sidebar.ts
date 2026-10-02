import { Locator, Page } from "@playwright/test";
import { TemplateModal } from "./templateModal";

export class Sidebar {
  page: Page;
  readonly root: Locator;
  readonly workspaceSelector: Locator;
  readonly workspaceMenuToggle: Locator;
  readonly logoutLink: Locator;
  readonly mySettingsLink: Locator;
  private createNewAppButton: Locator;
  private readonly createTemplateFromAppButton;

  constructor(page: Page) {
    this.page = page;
    this.root = page.locator(".sidebar");
    this.workspaceSelector = page.locator(".sidebar__workspaces-selector");
    // The name in the selector links to the workspaces homepage; the arrows
    // beside it open the menu.
    this.workspaceMenuToggle = page.locator(
      ".sidebar__workspaces-selector-toggle",
    );
    // The labels in this menu are translated, so anchor on the icons, which
    // are the same in every language.
    this.logoutLink = page.locator(
      ".context__menu-item-link:has(.iconoir-log-out)"
    );
    this.mySettingsLink = page.locator(
      ".context__menu-item-link:has(.iconoir-user-circle)"
    );
    // The "Add new..." label is translated; the element itself is not.
    this.createNewAppButton = page.locator(".sidebar__new");
    this.createTemplateFromAppButton = this.page
      .locator(".context__menu")
      .getByText("From template");
  }

  async selectDatabaseAndTableByName(dbName: string, tableName: string) {
    await this.selectDatabaseByName(dbName);
    await this.selectTableByName(tableName);
  }

  async selectDatabaseByName(name: string) {
    await this.root.getByTitle(name).click();
  }

  clickCreateNewApplication() {
    return this.createNewAppButton.click();
  }

  clickCreateNewAppFromTemplateButton() {
    return this.createTemplateFromAppButton.click();
  }

  async openCreateAppFromTemplateModal(): Promise<TemplateModal> {
    await this.clickCreateNewApplication();
    await this.clickCreateNewAppFromTemplateButton();
    const templateModal = new TemplateModal(this.page);
    await templateModal.waitUntilLoaded();
    return templateModal;
  }

  // Scoped to the sidebar and exact: the same table name usually also appears
  // in the dashboard behind it, and a substring match on a name like "Table"
  // also hits the "New table" link.
  async selectTableByName(name: string) {
    await this.root.locator(`.tree__sub-link[title="${name}"]`).click();
  }

  /**
   * Opens the menu behind the workspace selector, which holds the account
   * links (settings, log out).
   */
  async openUserContext() {
    await this.workspaceMenuToggle.click();
    await this.logoutLink.waitFor();
  }

  async logout() {
    await this.openUserContext();
    await this.logoutLink.click();
  }

  async openMySettings() {
    await this.openUserContext();
    await this.mySettingsLink.click();
  }

  /**
   * The names of the application types the "Add new..." menu offers.
   */
  async openCreateApplicationMenu(): Promise<Locator> {
    await this.clickCreateNewApplication();
    const menu = this.page.locator(".context__menu").last();
    await menu.waitFor();
    return menu;
  }
}
