import { expect, test } from "../jadawelTest";
import { createBuilder } from "../../fixtures/builder/builder";

/**
 * Jadawel fork: the application builder is hidden from the "Add new" menu of
 * users an administrator has not opened it to (docs/FEATURE_ACCESS.md), so
 * these tests create the application over the API, after `createBuilder`
 * grants the feature. That the creation option is gone without a grant is
 * asserted in tests/dashboard/createApplication.spec.ts.
 */
test.describe("Builder application test suite", () => {
  test("Can open an existing builder application", async ({
    page,
    builderPagePage,
  }) => {
    await builderPagePage.goto();

    await expect(
      page.locator(".page-editor").getByText("Page settings"),
      "Check we see the default page.",
    ).toBeVisible();
  });

  test("Can see a builder application by name in the sidebar", async ({
    page,
    workspacePage,
  }) => {
    await createBuilder("My super application", workspacePage.workspace);

    await workspacePage.goto();

    await expect(
      page.locator(".tree__link").getByText("My super application"),
      "Checks the name of the application is displayed in the sidebar.",
    ).toBeVisible();
  });
});
