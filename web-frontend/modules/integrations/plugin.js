import { defineNuxtPlugin } from '#app'

import { LocalJadawelIntegrationType } from '@jadawel/modules/integrations/localJadawel/integrationTypes'
import { SMTPIntegrationType } from '@jadawel/modules/integrations/core/integrationTypes'
import { AIIntegrationType } from '@jadawel/modules/integrations/ai/integrationTypes'
import {
  LocalJadawelGetRowServiceType,
  LocalJadawelListRowsServiceType,
  LocalJadawelAggregateRowsServiceType,
  LocalJadawelCreateRowWorkflowServiceType,
  LocalJadawelDeleteRowWorkflowServiceType,
  LocalJadawelUpdateRowWorkflowServiceType,
  LocalJadawelRowsCreatedTriggerServiceType,
  LocalJadawelRowsUpdatedTriggerServiceType,
  LocalJadawelRowsDeletedTriggerServiceType,
} from '@jadawel/modules/integrations/localJadawel/serviceTypes'
import {
  CoreInboundEmailTriggerServiceType,
  CoreHTTPRequestServiceType,
  PeriodicTriggerServiceType,
  CoreRouterServiceType,
  CoreSMTPEmailServiceType,
  CoreHTTPTriggerServiceType,
  CoreIteratorServiceType,
  CoreResponseServiceType,
} from '@jadawel/modules/integrations/core/serviceTypes'
import { AIAgentServiceType } from '@jadawel/modules/integrations/ai/serviceTypes'
import { SlackWriteMessageServiceType } from '@jadawel/modules/integrations/slack/serviceTypes'
import { SlackBotIntegrationType } from '@jadawel/modules/integrations/slack/integrationTypes'

export default defineNuxtPlugin({
  dependsOn: ['core'],
  setup(nuxtApp) {
    const { $registry } = nuxtApp

    const context = { app: nuxtApp }

    $registry.register('integration', new LocalJadawelIntegrationType(context))
    $registry.register('integration', new SMTPIntegrationType(context))
    $registry.register('integration', new AIIntegrationType(context))
    $registry.register('integration', new SlackBotIntegrationType(context))

    $registry.register('service', new LocalJadawelGetRowServiceType(context))
    $registry.register('service', new LocalJadawelListRowsServiceType(context))
    $registry.register(
      'service',
      new LocalJadawelAggregateRowsServiceType(context)
    )
    $registry.register(
      'service',
      new LocalJadawelCreateRowWorkflowServiceType(context)
    )
    $registry.register(
      'service',
      new LocalJadawelUpdateRowWorkflowServiceType(context)
    )
    $registry.register(
      'service',
      new LocalJadawelDeleteRowWorkflowServiceType(context)
    )
    $registry.register('service', new CoreHTTPRequestServiceType(context))
    $registry.register('service', new CoreSMTPEmailServiceType(context))
    $registry.register('service', new CoreRouterServiceType(context))
    $registry.register('service', new CoreHTTPTriggerServiceType(context))
    $registry.register(
      'service',
      new CoreInboundEmailTriggerServiceType(context)
    )
    $registry.register('service', new CoreIteratorServiceType(context))
    $registry.register('service', new CoreResponseServiceType(context))
    $registry.register('service', new AIAgentServiceType(context))
    $registry.register('service', new PeriodicTriggerServiceType(context))
    $registry.register('service', new SlackWriteMessageServiceType(context))
    $registry.register(
      'service',
      new LocalJadawelRowsCreatedTriggerServiceType(context)
    )
    $registry.register(
      'service',
      new LocalJadawelRowsUpdatedTriggerServiceType(context)
    )
    $registry.register(
      'service',
      new LocalJadawelRowsDeletedTriggerServiceType(context)
    )
  },
})
