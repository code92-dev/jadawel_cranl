import { expect, test } from "../jadawelTest";
import { createAutomation } from "../../fixtures/automation/automation";

/**
 * Jadawel fork: automations are hidden from the "Add new" menu (canBeCreated()
 * returns false in web-frontend/modules/automation/applicationTypes.js), so
 * these tests create the automation over the API — which is how an automation
 * that predates that change reaches its users. That the creation option is
 * gone is asserted in tests/dashboard/createApplication.spec.ts.
 */
test.describe("Automation application test suite", () => {
  test("Can open an existing automation on its workflow", async ({
    page,
    automationWorkflowPage,
  }) => {
    await automationWorkflowPage.goto();

    await expect(
      page.locator(".tree__link").getByText("Test automation"),
      "Ensure the automation name is displayed in the sidebar."
    ).toBeVisible();

    const workflowLink = page.getByRole("link", { name: "Default workflow" });
    await expect(
      workflowLink,
      "Ensure the workflow is visible."
    ).toBeVisible();

    // The start screen (recipes and events) of an empty workflow.
    const chooseTriggerTitle = page.getByText(
      "How should this workflow start?"
    );
    await expect(
      chooseTriggerTitle,
      "Ensure the start screen is visible."
    ).toBeVisible();
  });

  test("Can see an automation by name in the sidebar", async ({
    page,
    workspacePage,
  }) => {
    await createAutomation("Foo Automation", workspacePage.workspace);

    await workspacePage.goto();

    await expect(
      page.locator(".tree__link").getByText("Foo Automation"),
      "Ensure the custom automation name is displayed in the sidebar."
    ).toBeVisible();
  });
});
