import { getClient } from "../../client"
import { grantFeature } from "../featureAccess"
import { Workspace } from "../workspace"

export class Automation {
  constructor(
    public id: number,
    public name: string,
    public workspace: Workspace
  ) {}
}

export async function createAutomation(
  automationName: string,
  workspace: Workspace
): Promise<Automation> {
  await grantFeature(workspace.user, "automation")
  const response: any = await getClient(workspace.user).post(
    `applications/workspace/${workspace.id}/`,
    {
      name: automationName,
      type: "automation",
    }
  )
  return new Automation(response.data.id, response.data.name, workspace)
}
