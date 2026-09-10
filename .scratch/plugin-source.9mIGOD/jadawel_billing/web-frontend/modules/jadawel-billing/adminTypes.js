import { AdminType } from "@jadawel/modules/core/adminTypes";

export class BillingAdminType extends AdminType {
  static getType() {
    return "jadawel_billing";
  }
  getIconClass() {
    return "iconoir-credit-card";
  }
  getName() {
    return this.app.$i18n.t("billing.title");
  }
  getRouteName() {
    return "admin-billing";
  }
  getOrder() {
    return 10200;
  }
}
