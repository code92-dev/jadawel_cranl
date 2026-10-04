import { getClient } from "../client";
import { getStaffUser, User } from "./user";

export type Feature = "automation" | "builder" | "sanad";

/**
 * Jadawel fork: creating an automation or an application, and using Sanad,
 * needs the feature (docs/FEATURE_ACCESS.md). The e2e staff user grants it to
 * the test user's email address, as an administrator would; granting an
 * address twice changes nothing.
 */
export async function grantFeature(user: User, feature: Feature): Promise<void> {
  const staff = await getStaffUser();
  await getClient(staff).post(
    `arabase/admin/feature-access/${feature}/grants/`,
    { emails: [user.email] }
  );
}
