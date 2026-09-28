/**
 * The steps of an automation, as the redesigned editor presents them: every
 * node type in a category that says what it is for, with a colour tone, an
 * icon and — in the locales — a plain-language name and one line on when to
 * use it ("Add a row", "Send an email"). The same catalogue drives the start
 * screen, the step gallery, the cards on the canvas and the overview strip.
 * docs/AUTOMATION_REDESIGN.md explains the choices.
 */
import NodeGraphHandler from '@jadawel/modules/automation/utils/nodeGraphHandler'
import { isSubstringOfStrings } from '@jadawel/modules/core/utils/string'
import { pluralKeys } from '@jadawel/modules/core/utils/plural'

/** What starts a workflow, in the order the start screen shows them. */
export const TRIGGER_CATEGORIES = ['records', 'schedule', 'web']

/** What a step does, in the order the step gallery shows them. */
export const ACTION_CATEGORIES = ['records', 'messages', 'logic', 'ai', 'web']

/** Each category's colour: one hue per job, never the only signal. */
export const CATEGORY_TONES = {
  records: 'green',
  schedule: 'amber',
  messages: 'blue',
  logic: 'purple',
  ai: 'magenta',
  web: 'cyan',
}

/**
 * Every node type the fork knows. Order within a category follows this list.
 * `icon` replaces the service's own icon, which for the table events was a
 * bare "+".
 */
export const STEP_CATALOG = {
  local_jadawel_rows_created: {
    category: 'records',
    icon: 'iconoir-add-square',
  },
  local_jadawel_rows_updated: {
    category: 'records',
    icon: 'iconoir-edit-pencil',
  },
  local_jadawel_rows_deleted: { category: 'records', icon: 'iconoir-trash' },
  periodic: { category: 'schedule', icon: 'iconoir-clock' },
  http_trigger: { category: 'web', icon: 'iconoir-globe' },
  local_jadawel_create_row: { category: 'records', icon: 'iconoir-add-square' },
  local_jadawel_update_row: {
    category: 'records',
    icon: 'iconoir-edit-pencil',
  },
  local_jadawel_get_row: { category: 'records', icon: 'iconoir-search' },
  local_jadawel_list_rows: { category: 'records', icon: 'iconoir-list' },
  local_jadawel_aggregate_rows: {
    category: 'records',
    icon: 'iconoir-calculator',
  },
  local_jadawel_delete_row: { category: 'records', icon: 'iconoir-trash' },
  smtp_email: { category: 'messages', icon: 'iconoir-mail' },
  slack_write_message: {
    category: 'messages',
    icon: 'iconoir-chat-bubble',
    // Slack's own logo says more than any icon.
    logo: true,
  },
  router: { category: 'logic', icon: 'iconoir-git-fork' },
  iterator: { category: 'logic', icon: 'iconoir-repeat' },
  ai_agent: { category: 'ai', icon: 'iconoir-sparks' },
  http_request: { category: 'web', icon: 'iconoir-send' },
}

/** A node type's place in the catalogue; unknown types fall back sensibly. */
export function stepEntry(nodeType) {
  const type = nodeType?.getType ? nodeType.getType() : nodeType?.type
  const known = STEP_CATALOG[type]
  const category =
    known?.category || (nodeType?.isTrigger ? 'records' : 'logic')
  return {
    type,
    known: Boolean(known),
    category,
    tone: CATEGORY_TONES[category],
    icon: known?.icon || nodeType?.iconClass || 'iconoir-flash',
    // The service's image instead of the icon: a brand's logo, or whatever
    // an unknown type brings.
    image: (!known || known.logo ? nodeType?.image : null) || null,
  }
}

/**
 * A counted message in the reader's plural form ("3 steps", "3 خطوات"): the
 * CLDR category picks a plain key, as `core/utils/plural.js` explains.
 */
export function counted(vm, base, count, values = {}) {
  const keys = pluralKeys(base, vm.$i18n.locale, count)
  const key = keys.find((candidate) => vm.$te(candidate)) || keys.at(-1)
  return vm.$t(key, { count, ...values })
}

/**
 * A step type's plain-language name ("Add a row") — the catalogue's, or the
 * service's own for a type the fork does not describe. `vm` is anything with
 * `$t`.
 */
export function stepName(vm, nodeType) {
  return stepEntry(nodeType).known
    ? vm.$t(`automationSteps.types.${nodeType.getType()}.name`)
    : nodeType.name
}

/** One line on when to use a step type. */
export function stepDescription(vm, nodeType) {
  return stepEntry(nodeType).known
    ? vm.$t(`automationSteps.types.${nodeType.getType()}.description`)
    : nodeType.description
}

/**
 * The gallery's sections for triggers or actions: the node types matching
 * `search` (by name, description or the catalogue's own words), grouped and
 * ordered. Empty sections are left out.
 */
export function stepSections(
  nodeTypes,
  { trigger = false, search = '', describe = () => [] } = {}
) {
  const order = Object.keys(STEP_CATALOG)
  const position = (type) => {
    const index = order.indexOf(type.getType())
    return index === -1 ? order.length : index
  }
  const matching = nodeTypes
    .filter((type) =>
      isSubstringOfStrings(
        [type.name || '', type.description || '', ...describe(type)],
        search
      )
    )
    .sort((a, b) => position(a) - position(b))
  const categories = trigger ? TRIGGER_CATEGORIES : ACTION_CATEGORIES
  return categories
    .map((category) => ({
      category,
      tone: CATEGORY_TONES[category],
      nodeTypes: matching.filter(
        (type) => stepEntry(type).category === category
      ),
    }))
    .filter((section) => section.nodeTypes.length > 0)
}

/**
 * The workflow's steps in reading order: the trigger, then each step, a
 * container's children before what follows it, a router's branches in turn.
 */
export function orderedNodes(workflow) {
  if (!workflow?.graph || !workflow?.nodeMap) {
    return []
  }
  const graph = new NodeGraphHandler(workflow)
  const seen = new Set()
  const ordered = []
  const visit = (node) => {
    if (!node || seen.has(node.id)) {
      return
    }
    seen.add(node.id)
    ordered.push(node)
    graph.getChildren(node).forEach(visit)
    graph.getNextNodes(node).forEach(visit)
  }
  visit(graph.getFirstNode())
  return ordered
}

function inError(nodeType, node) {
  try {
    return Boolean(nodeType.isInError({ service: node.service, node }))
  } catch (error) {
    // A step whose type cannot judge its own settings is not blocked on it.
    return false
  }
}

/**
 * Where a workflow stands: its steps in order, each with its type, catalogue
 * entry and whether it still needs setting up, and the first one that does.
 */
export function workflowReadiness(workflow, registry) {
  const steps = orderedNodes(workflow)
    .filter((node) => registry.exists('node', node.type))
    .map((node, index) => {
      const nodeType = registry.get('node', node.type)
      const needsSetup = inError(nodeType, node)
      return {
        node,
        nodeType,
        number: index + 1,
        needsSetup,
        ...stepEntry(nodeType),
      }
    })
  const ready = steps.filter((step) => !step.needsSetup).length
  return {
    steps,
    ready,
    total: steps.length,
    next: steps.find((step) => step.needsSetup) || null,
  }
}
