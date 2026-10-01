import CoreHTTPTriggerServiceForm from '@jadawel/modules/integrations/core/components/services/CoreHTTPTriggerServiceForm'
import CoreInboundEmailTriggerServiceForm from '@jadawel/modules/integrations/core/components/services/CoreInboundEmailTriggerServiceForm'
import {
  ServiceType,
  TriggerServiceTypeMixin,
  WorkflowActionServiceTypeMixin,
} from '@jadawel/modules/core/serviceTypes'
import CoreHTTPRequestServiceForm from '@jadawel/modules/integrations/core/components/services/CoreHTTPRequestServiceForm'
import CoreSMTPEmailServiceForm from '@jadawel/modules/integrations/core/components/services/CoreSMTPEmailServiceForm'
import CoreRouterServiceForm from '@jadawel/modules/integrations/core/components/services/CoreRouterServiceForm'
import CoreIteratorServiceForm from '@jadawel/modules/integrations/core/components/services/CoreIteratorServiceForm'
import CorePeriodicServiceForm from '@jadawel/modules/integrations/core/components/services/CorePeriodicServiceForm.vue'
import CoreResponseServiceForm from '@jadawel/modules/integrations/core/components/services/CoreResponseServiceForm.vue'

export class CoreHTTPRequestServiceType extends WorkflowActionServiceTypeMixin(
  ServiceType
) {
  static getType() {
    return 'http_request'
  }

  get icon() {
    return 'iconoir-cloud-upload'
  }

  get name() {
    return this.app.$i18n.t('serviceType.coreHTTPRequest')
  }

  get description() {
    return this.app.$i18n.t('serviceType.coreHTTPRequestDescription')
  }

  getErrorMessage({ service }) {
    // We check undefined because the url is not returned in public mode the
    // property is just ignored
    if (
      service !== undefined &&
      service.url !== undefined &&
      !service.url.formula
    ) {
      return this.app.$i18n.t('serviceType.errorUrlMissing')
    }

    return super.getErrorMessage({ service })
  }

  getDataSchema(service) {
    return service.schema
  }

  get formComponent() {
    return CoreHTTPRequestServiceForm
  }

  getOrder() {
    return 5
  }
}

export class CoreSMTPEmailServiceType extends WorkflowActionServiceTypeMixin(
  ServiceType
) {
  static getType() {
    return 'smtp_email'
  }

  get name() {
    return this.app.$i18n.t('serviceType.coreSMTPEmail')
  }

  get description() {
    return this.app.$i18n.t('serviceType.coreSMTPEmailDescription')
  }

  get icon() {
    return 'iconoir-send-mail'
  }

  getErrorMessage({ service }) {
    if (
      service === undefined ||
      // This case happens in a published application. We don't want to check
      // the validity in that case.
      service.use_instance_smtp_settings === undefined
    ) {
      return null
    }

    if (!service.use_instance_smtp_settings && !service.integration_id) {
      return this.app.$i18n.t('serviceType.errorNoIntegrationSelected')
    }

    if (
      !service.use_instance_smtp_settings &&
      service.from_email !== undefined &&
      !service.from_email.formula
    ) {
      return this.app.$i18n.t('serviceType.errorFromEmailMissing')
    }

    if (service.to_emails !== undefined && !service.to_emails.formula) {
      return this.app.$i18n.t('serviceType.errorToEmailsMissing')
    }

    return super.getErrorMessage({ service })
  }

  getDataSchema(service) {
    return service.schema
  }

  get formComponent() {
    return CoreSMTPEmailServiceForm
  }

  getOrder() {
    return 6
  }
}

export class CoreRouterServiceType extends WorkflowActionServiceTypeMixin(
  ServiceType
) {
  static getType() {
    return 'router'
  }

  get name() {
    return this.app.$i18n.t('serviceType.coreRouter')
  }

  get description() {
    return this.app.$i18n.t('serviceType.coreRouterDescription')
  }

  get icon() {
    return 'iconoir-git-fork'
  }

  getEdgeErrorMessage(edge) {
    if (!edge.label.length) {
      return this.app.$i18n.t('serviceType.coreRouterEdgeLabelRequired')
    } else if (!edge.condition.formula) {
      return this.app.$i18n.t('serviceType.coreRouterEdgeConditionRequired')
    }
    return null
  }

  getErrorMessage({ service }) {
    if (service === undefined) {
      return null
    }
    if (!service.edges?.length) {
      return this.app.$i18n.t('serviceType.coreRouterEdgesRequired')
    }
    for (const edge of service.edges) {
      const errorMessage = this.getEdgeErrorMessage(edge)
      if (errorMessage) {
        return errorMessage
      }
    }
    return super.getErrorMessage({ service })
  }

  getDataSchema(service) {
    return service.schema
  }

  get formComponent() {
    return CoreRouterServiceForm
  }

  getOrder() {
    return 7
  }
}

export class CoreHTTPTriggerServiceType extends TriggerServiceTypeMixin(
  ServiceType
) {
  static getType() {
    return 'http_trigger'
  }

  get name() {
    return this.app.$i18n.t('serviceType.coreHTTPTrigger')
  }

  get description() {
    return this.app.$i18n.t('serviceType.coreHTTPTriggerDescription')
  }

  get formComponent() {
    return CoreHTTPTriggerServiceForm
  }

  get icon() {
    return 'iconoir-globe'
  }

  getErrorMessage({ service }) {
    if (service === undefined) {
      return null
    }

    return super.getErrorMessage({ service })
  }

  getDataSchema(service) {
    return service.schema
  }

  getOrder() {
    return 8
  }
}

export class CoreInboundEmailTriggerServiceType extends TriggerServiceTypeMixin(
  ServiceType
) {
  static getType() {
    return 'email_trigger'
  }

  get name() {
    return this.app.$i18n.t('serviceType.inboundEmailTrigger')
  }

  get description() {
    return this.app.$i18n.t('serviceType.inboundEmailTriggerDescription')
  }

  get formComponent() {
    return CoreInboundEmailTriggerServiceForm
  }

  get icon() {
    return 'iconoir-mail'
  }

  getErrorMessage({ service }) {
    if (service === undefined) {
      return null
    }

    return super.getErrorMessage({ service })
  }

  getDataSchema(service) {
    return service.schema
  }

  /**
   * The sample data is a received email, so the sample data modal offers an
   * HTML preview tab next to the JSON payload.
   */
  getSampleDataContentType(service) {
    return 'html'
  }

  getSampleDataHtml(service) {
    return service.sample_data?.data?.body_html || null
  }

  getOrder() {
    return 8.5
  }
}

export class CoreIteratorServiceType extends WorkflowActionServiceTypeMixin(
  ServiceType
) {
  static getType() {
    return 'iterator'
  }

  get name() {
    return this.app.$i18n.t('serviceType.coreIteration')
  }

  get description() {
    return this.app.$i18n.t('serviceType.coreIterationDescription')
  }

  get icon() {
    return 'iconoir-repeat'
  }

  getErrorMessage({ service }) {
    if (!service?.source?.formula) {
      return this.app.$i18n.t('serviceType.errorIterationSourceMissing')
    }

    return super.getErrorMessage({ service })
  }

  getDataSchema(service) {
    return service.schema
  }

  get formComponent() {
    return CoreIteratorServiceForm
  }

  getOrder() {
    return 5
  }
}

export class CoreResponseServiceType extends WorkflowActionServiceTypeMixin(
  ServiceType
) {
  static getType() {
    return 'response'
  }

  get name() {
    return this.app.$i18n.t('serviceType.coreResponse')
  }

  get description() {
    return this.app.$i18n.t('serviceType.coreResponseDescription')
  }

  get icon() {
    return 'iconoir-reply'
  }

  get formComponent() {
    return CoreResponseServiceForm
  }

  getDataSchema(service) {
    return service.schema
  }

  getErrorMessage(params) {
    const { service } = params
    // The node's service is not there yet while a step is being created.
    if (service === undefined) {
      return null
    }
    const isNoContentResponse =
      service.status_code?.mode === 'raw' &&
      service.status_code.formula === '204'
    if (
      !isNoContentResponse &&
      service.body_type === 'json' &&
      !service.body?.formula?.trim()
    ) {
      return this.app.$i18n.t('serviceType.errorResponseBodyMissing')
    }
    return super.getErrorMessage(params)
  }

  getOrder() {
    return 9
  }
}

export class PeriodicTriggerServiceType extends TriggerServiceTypeMixin(
  ServiceType
) {
  static getType() {
    return 'periodic'
  }

  get name() {
    return this.app.$i18n.t('serviceType.corePeriodic')
  }

  get description() {
    return this.app.$i18n.t('serviceType.corePeriodicDescription')
  }

  get formComponent() {
    return CorePeriodicServiceForm
  }

  get icon() {
    return 'iconoir-timer'
  }

  getDataSchema(service) {
    return service.schema
  }

  getErrorMessage({ service }) {
    if (!service?.interval) {
      return this.app.$i18n.t('serviceType.corePeriodicErrorIntervalMissing')
    }
    return super.getErrorMessage({ service })
  }
}
