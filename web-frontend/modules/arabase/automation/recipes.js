/**
 * Recipes: whole workflows for the jobs people automate most, built in one
 * click from the start screen — the trigger and every step, in order, each
 * with a name that says what it is for. What is left is choosing the tables
 * and writing the message, which the canvas marks as "Needs setup".
 *
 * Between them the recipes use every event and every step the editor offers
 * (`recipes.spec.js` fails otherwise), so each can be met in a working flow.
 *
 * A step is a node type, or `{ type, children }` for a container whose steps
 * run inside it (a loop). A recipe with a `schedule` sets its periodic trigger
 * to it, in the local time of whoever builds it; `triggerValues` are set on the
 * trigger's service as they are. Names and descriptions are in
 * the locales under `automationRecipes.recipes.<key>`; the step names are
 * `labels.trigger`, then `labels.step1`… in reading order, children included.
 */
import AutomationWorkflowNodeService from '@jadawel/modules/automation/services/automationWorkflowNode'

/** The start screen's recipe groups, in order. */
export const RECIPE_CATEGORIES = ['notify', 'records', 'schedule', 'connect']

export const RECIPES = [
  // Tell people
  {
    key: 'email_new_row',
    category: 'notify',
    trigger: 'local_jadawel_rows_created',
    steps: ['smtp_email'],
  },
  {
    key: 'slack_new_row',
    category: 'notify',
    trigger: 'local_jadawel_rows_created',
    steps: ['slack_write_message'],
  },
  {
    key: 'email_on_change',
    category: 'notify',
    trigger: 'local_jadawel_rows_updated',
    steps: ['smtp_email'],
  },
  {
    key: 'email_related_person',
    category: 'notify',
    trigger: 'local_jadawel_rows_created',
    steps: ['local_jadawel_get_row', 'smtp_email'],
  },
  // Keep tables in order
  {
    key: 'task_for_new_row',
    category: 'records',
    trigger: 'local_jadawel_rows_created',
    steps: ['local_jadawel_create_row'],
  },
  {
    key: 'archive_finished_rows',
    category: 'records',
    trigger: 'local_jadawel_rows_updated',
    steps: ['local_jadawel_create_row', 'local_jadawel_delete_row'],
  },
  {
    key: 'log_deleted_rows',
    category: 'records',
    trigger: 'local_jadawel_rows_deleted',
    steps: ['local_jadawel_create_row'],
  },
  {
    key: 'email_to_row',
    category: 'records',
    trigger: 'email_trigger',
    steps: ['local_jadawel_create_row'],
  },
  // On a schedule
  {
    key: 'daily_digest',
    category: 'schedule',
    trigger: 'periodic',
    steps: ['local_jadawel_list_rows', 'smtp_email'],
    // Every day at 08:00, as its name says.
    schedule: { interval: 'DAY', hour: 8, minute: 0 },
  },
  {
    key: 'overdue_reminders',
    category: 'schedule',
    trigger: 'periodic',
    steps: [
      'local_jadawel_list_rows',
      { type: 'iterator', children: ['smtp_email'] },
    ],
    schedule: { interval: 'DAY', hour: 8, minute: 0 },
  },
  {
    key: 'weekly_totals',
    category: 'schedule',
    trigger: 'periodic',
    steps: ['local_jadawel_aggregate_rows', 'smtp_email'],
    // Sundays at 08:00, the start of the Saudi working week (0 is Monday).
    schedule: { interval: 'WEEK', day_of_week: 6, hour: 8, minute: 0 },
  },
  {
    key: 'weekly_slack_summary',
    category: 'schedule',
    trigger: 'periodic',
    steps: ['local_jadawel_aggregate_rows', 'slack_write_message'],
    schedule: { interval: 'WEEK', day_of_week: 6, hour: 8, minute: 0 },
  },
  // Connect and decide
  {
    key: 'web_request_to_row',
    category: 'connect',
    trigger: 'http_trigger',
    steps: ['local_jadawel_create_row'],
  },
  {
    key: 'answer_web_request',
    category: 'connect',
    trigger: 'http_trigger',
    steps: ['local_jadawel_get_row', 'response'],
    // The caller waits for the Response step's answer.
    triggerValues: { wait_for_response: true },
  },
  {
    key: 'send_to_system',
    category: 'connect',
    trigger: 'local_jadawel_rows_created',
    steps: ['http_request'],
  },
  {
    key: 'route_by_value',
    category: 'connect',
    trigger: 'local_jadawel_rows_updated',
    steps: ['router'],
  },
  {
    key: 'ai_fill_row',
    category: 'connect',
    trigger: 'local_jadawel_rows_created',
    steps: ['ai_agent', 'local_jadawel_update_row'],
  },
]

function asStep(step) {
  return typeof step === 'string' ? { type: step, children: [] } : step
}

/**
 * Every node type a recipe creates, in the order it creates them: the
 * trigger, then each step followed by the steps inside it.
 */
export function recipeTypes(recipe) {
  return [
    recipe.trigger,
    ...recipe.steps.flatMap((step) => {
      const { type, children = [] } = asStep(step)
      return [type, ...children]
    }),
  ]
}

/**
 * A periodic trigger's service values for a schedule in local time. The
 * service stores UTC (as `CorePeriodicServiceForm` does, which shows them back
 * in local time), so 08:00 in Riyadh is stored as 05:00. `day_of_week` counts
 * from Monday (0) to Sunday (6).
 */
export function scheduleValues(schedule, now = new Date()) {
  const local = new Date(now)
  if (schedule.day_of_week !== undefined) {
    const today = (local.getDay() + 6) % 7
    local.setDate(local.getDate() + schedule.day_of_week - today)
  }
  local.setHours(schedule.hour ?? 0, schedule.minute ?? 0, 0, 0)
  const values = {
    interval: schedule.interval,
    hour: local.getUTCHours(),
    minute: local.getUTCMinutes(),
  }
  if (schedule.day_of_week !== undefined) {
    values.day_of_week = (local.getUTCDay() + 6) % 7
  }
  return values
}

/**
 * The recipes whose every node type is registered here and enabled on this
 * instance (the email trigger needs inbound email configured).
 */
export function availableRecipes(registry) {
  const usable = (type) =>
    registry.exists('node', type) &&
    (registry.get?.('node', type).isEnabled?.() ?? true)
  return RECIPES.filter((recipe) => recipeTypes(recipe).every(usable))
}

/** The available recipes by group, groups without a recipe left out. */
export function recipeSections(registry) {
  const recipes = availableRecipes(registry)
  return RECIPE_CATEGORIES.map((category) => ({
    category,
    recipes: recipes.filter((recipe) => recipe.category === category),
  })).filter((section) => section.recipes.length > 0)
}

/** The locale keys of a recipe's step names, in the order they are created. */
export function recipeLabelKeys(recipe) {
  const base = `automationRecipes.recipes.${recipe.key}.labels`
  return recipeTypes(recipe).map((_, index) =>
    index === 0 ? `${base}.trigger` : `${base}.step${index}`
  )
}

/**
 * Builds `recipe` in an empty `workflow`: the trigger, then each step after
 * the previous one (a container's steps inside it), then names them all and
 * sets the schedule. Resolves to the created nodes; the trigger is left
 * selected, so its settings open first. A failure stops the build where it
 * is: what was created stays, like any step added by hand.
 */
export async function buildRecipe({ store, client, workflow, recipe, labels }) {
  const created = []
  const add = async (type, referenceNode, position) => {
    const node = await store.dispatch('automationWorkflowNode/create', {
      workflow,
      type,
      referenceNode,
      position: referenceNode ? position : undefined,
      output: referenceNode ? '' : undefined,
    })
    created.push(node)
    return node
  }

  let previous = await add(recipe.trigger, null)
  for (const step of recipe.steps) {
    const { type, children = [] } = asStep(step)
    const node = await add(type, previous, 'south')
    let inside = null
    for (const child of children) {
      inside = await add(child, inside || node, inside ? 'south' : 'child')
    }
    previous = node
  }

  const service = AutomationWorkflowNodeService(client)
  await Promise.all(
    created.map(async (node, index) => {
      const stored = store.getters['automationWorkflowNode/findById'](
        workflow,
        node.id
      )
      const values = {}
      if (labels[index]) {
        values.label = labels[index]
      }
      if (index === 0 && (recipe.schedule || recipe.triggerValues)) {
        values.service = {
          ...(stored?.service || node.service),
          ...(recipe.schedule ? scheduleValues(recipe.schedule) : {}),
          ...(recipe.triggerValues || {}),
        }
      }
      if (Object.keys(values).length === 0) {
        return
      }
      const { data } = await service.update(node.id, values)
      if (stored) {
        store.dispatch('automationWorkflowNode/forceUpdate', {
          workflow,
          node: stored,
          values: data && data.id ? data : values,
        })
      }
    })
  )

  const trigger = store.getters['automationWorkflowNode/findById'](
    workflow,
    created[0].id
  )
  // After the selection each `create` schedules for its own node.
  setTimeout(() => {
    store.dispatch('automationWorkflowNode/select', {
      workflow,
      node: trigger,
    })
  })
  return created
}
