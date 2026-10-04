import { expect, test } from "../jadawelTest";

test.describe("Creating applications from the sidebar", () => {
  test.beforeEach(async ({ workspacePage }) => {
    await workspacePage.goto();
  });

  test("A user can create a database and open its first table", async ({
    page,
    workspacePage,
  }) => {
    const menu = await workspacePage.sidebar.openCreateApplicationMenu();
    await menu.getByText("Database", { exact: true }).click();

    const modal = page.locator(".modal__box").last();
    await modal.locator("input").first().fill("Sales pipeline");
    await modal.locator("form button").last().click();

    await expect(
      workspacePage.sidebar.root.getByTitle("Sales pipeline"),
      "The new database shows up in the sidebar."
    ).toBeVisible();

    await workspacePage.sidebar.selectTableByName("Table");
    await expect(
      page.locator(".grid-view"),
      "Its default table opens in the grid view."
    ).toBeVisible();
  });

  /**
   * This fork hides the application builder and automations from the create
   * menu (see canBeCreated() in their applicationTypes.js) of users an
   * administrator has not opened them to (docs/FEATURE_ACCESS.md). A new user
   * has no grant. Existing applications keep working.
   */
  test("The builder and automations are not offered as new applications @fast", async ({
    workspacePage,
  }) => {
    const menu = await workspacePage.sidebar.openCreateApplicationMenu();

    await expect(menu, "Databases can be created.").toContainText("Database");
    await expect(menu, "The builder is hidden.").not.toContainText(
      "Application"
    );
    await expect(menu, "Automations are hidden.").not.toContainText(
      "Automation"
    );
  });
});
