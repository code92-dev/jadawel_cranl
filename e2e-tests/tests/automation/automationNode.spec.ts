import { expect, test } from "../jadawelTest";

import { createAutomationNode } from "../../fixtures/automation/automationNode";

test.describe("Automation node test suite", () => {
  let trigger;
  // The automation editor does not subscribe to realtime page updates the way
  // the database module does, so a node created over the API only shows up if
  // it already exists when the workflow page fetches its nodes. Create it
  // first and open the page afterwards, otherwise the test is a race against
  // that fetch.
  test.beforeEach(async ({ automationWorkflowPage, page }) => {
    trigger = await createAutomationNode(
      automationWorkflowPage.automationWorkflow,
      "periodic"
    );

    await automationWorkflowPage.goto();

    // The unconfigured trigger's card says so.
    const needsSetup = page
      .locator(".workflow-node-content__status")
      .getByText("Needs setup");
    await expect(needsSetup).toBeVisible();
  });

  test("Can create an automation node", async ({ page }) => {
    const createNodeButton = page.getByRole("button", {
      name: "Create automation node",
    });
    await createNodeButton.click();

    // The step gallery names steps in plain words; the card keeps the
    // service's label.
    const rowsCreatedOption = page
      .locator(".step-gallery__item")
      .getByText("Add a row", { exact: true });
    await expect(rowsCreatedOption).toBeVisible();
    await rowsCreatedOption.click();

    const nodeDiv = page.getByRole("heading", {
      name: "Create a row",
      level: 1,
    });
    await expect(nodeDiv).toBeVisible();
  });

  test("Can delete an automation node", async ({
    page,
    automationWorkflowPage,
  }) => {
    await createAutomationNode(
      automationWorkflowPage.automationWorkflow,
      "local_jadawel_create_row",
      trigger.id,
      "south",
      ""
    );

    // Same reason as in beforeEach: reopen the page so the new node is part of
    // the fetched workflow.
    await automationWorkflowPage.goto();

    const nodeDiv = page.getByRole("heading", {
      name: "Create a row",
      level: 1,
    });
    await expect(nodeDiv).toBeVisible();

    // Let's select the node
    await nodeDiv.click();

    await page.locator(".vue-flow__controls-fitview").click();

    const nodeMenuButton = page
      .locator(".workflow-node-content--selected")
      .getByRole("button", { name: "Node options" });
    await nodeMenuButton.click();

    const deleteNodeButton = page.getByRole("button", { name: "Delete" });
    await deleteNodeButton.waitFor({ state: "visible" });
    deleteNodeButton.click();

    await expect(nodeDiv).not.toBeVisible();
  });
});
