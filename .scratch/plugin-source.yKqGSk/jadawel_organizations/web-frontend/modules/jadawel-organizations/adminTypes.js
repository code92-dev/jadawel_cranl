import { AdminType } from "@jadawel/modules/core/adminTypes";

export class OrganizationsAdminType extends AdminType {
  static getType() {
    return "jadawel_organizations";
  }

  getIconClass() {
    return "iconoir-community";
  }

  getName() {
    return this.app.$i18n.t("organizations.adminTitle");
  }

  getRouteName() {
    return "admin-organizations";
  }

  getOrder() {
    return 10300;
  }
}
