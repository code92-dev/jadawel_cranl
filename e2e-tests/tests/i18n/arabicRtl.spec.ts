import { expect, test } from "../jadawelTest";
import { LoginPage } from "../../pages/loginPage";
import { SettingsModal } from "../../pages/components/settingsModal";

const ARABIC = "العربية";
const ENGLISH = "English";

/**
 * Jadawel is an Arabic first, right to left fork, so the direction of the
 * document is a product requirement rather than cosmetics.
 */
test.describe("Arabic and right to left layout", () => {
  test.describe("with an Arabic browser", () => {
    test.use({ locale: "ar-SA" });

    test("The login page is served in Arabic and right to left @fast", async ({
      page,
      goto,
    }) => {
      const loginPage = new LoginPage({ page, goto });
      await loginPage.goto();

      await expect(
        page.locator("html"),
        "The document direction follows the Arabic locale."
      ).toHaveAttribute("dir", "rtl");
      await expect(page.locator("html")).toHaveAttribute("lang", "ar");
      await expect(
        loginPage.loginButton,
        "The submit button is translated."
      ).toContainText("تسجيل الدخول");
    });

    test("An Arabic visitor can switch the login page to English @fast", async ({
      page,
      goto,
    }) => {
      const loginPage = new LoginPage({ page, goto });
      await loginPage.goto();

      await loginPage.selectLanguage(ENGLISH);

      await expect(
        page.locator("html"),
        "Choosing English flips the document back to left to right."
      ).toHaveAttribute("dir", "ltr");
      await expect(loginPage.loginButton).toContainText("Login");
    });
  });

  test("Switching the interface language to Arabic flips the app to RTL", async ({
    page,
    workspacePage,
  }) => {
    await workspacePage.goto();
    await expect(page.locator("html")).toHaveAttribute("dir", "ltr");

    await workspacePage.sidebar.openMySettings();
    const settingsModal = new SettingsModal(page);
    await settingsModal.waitUntilLoaded();
    await settingsModal.setInterfaceLanguage(ARABIC);

    await expect(
      page.locator("html"),
      "The whole app switches to right to left."
    ).toHaveAttribute("dir", "rtl");
    await expect(page.locator("html")).toHaveAttribute("lang", "ar");

    await page.reload();

    await expect(
      page.locator("html"),
      "The language choice is stored on the account and survives a reload."
    ).toHaveAttribute("dir", "rtl");
    await expect(
      workspacePage.sidebar.root,
      "The sidebar is translated after the switch."
    ).toContainText("الأحدث");
  });
});
