// NB: no locale imports here. Translations are registered centrally from
// config/locales.js via each module's module.js; these were dead imports that
// bound nothing, and they broke the build once the files were removed.
import {
  GeneralBuilderSettingsType,
  DomainsBuilderSettingsType,
  IntegrationsBuilderSettingsType,
  ThemeBuilderSettingsType,
  UserSourcesBuilderSettingsType,
} from '@jadawel/modules/builder/builderSettingTypes'

import pageStore from '@jadawel/modules/builder/store/page'
import elementStore from '@jadawel/modules/builder/store/element'
import domainStore from '@jadawel/modules/builder/store/domain'
import publicBuilderStore from '@jadawel/modules/builder/store/publicBuilder'
import dataSourceStore from '@jadawel/modules/builder/store/dataSource'
import pageParameterStore from '@jadawel/modules/builder/store/pageParameter'
import dataSourceContentStore from '@jadawel/modules/builder/store/dataSourceContent'
import elementContentStore from '@jadawel/modules/builder/store/elementContent'
import themeStore from '@jadawel/modules/builder/store/theme'
import builderWorkflowActionStore from '@jadawel/modules/builder/store/builderWorkflowAction'
import formDataStore from '@jadawel/modules/builder/store/formData'
import builderToast from '@jadawel/modules/builder/store/builderToast'
import { registerRealtimeEvents } from '@jadawel/modules/builder/realtime'
import {
  HeadingElementType,
  ImageElementType,
  TextElementType,
  LinkElementType,
  InputTextElementType,
  ColumnElementType,
  ButtonElementType,
  TableElementType,
  FormContainerElementType,
  ChoiceElementType,
  CheckboxElementType,
  DateTimePickerElementType,
  IFrameElementType,
  RepeatElementType,
  RecordSelectorElementType,
  HeaderElementType,
  FooterElementType,
  RatingElementType,
  RatingInputElementType,
  MenuElementType,
  SimpleContainerElementType,
} from '@jadawel/modules/builder/elementTypes'
import {
  DesktopDeviceType,
  SmartphoneDeviceType,
  TabletDeviceType,
} from '@jadawel/modules/builder/deviceTypes'
import {
  DuplicatePageJobType,
  PublishBuilderJobType,
} from '@jadawel/modules/builder/jobTypes'
import { BuilderApplicationType } from '@jadawel/modules/builder/applicationTypes'
import { BuilderPageLastViewedItemType } from '@jadawel/modules/builder/lastViewedItemTypes'
import { PublicSiteErrorPageType } from '@jadawel/modules/builder/errorPageTypes'
import {
  DataSourcesPageHeaderItemType,
  ElementsPageHeaderItemType,
  SettingsPageHeaderItemType,
} from '@jadawel/modules/builder/pageHeaderItemTypes'
import {
  EventsPageSidePanelType,
  GeneralPageSidePanelType,
  StylePageSidePanelType,
  VisibilityPageSidePanelType,
} from '@jadawel/modules/builder/pageSidePanelTypes'
import {
  CustomDomainType,
  SubDomainType,
} from '@jadawel/modules/builder/domainTypes'
import {
  PagePageSettingsType,
  PageVisibilitySettingsType,
} from '@jadawel/modules/builder/pageSettingsTypes'
import {
  TextPathParamType,
  NumericPathParamType,
} from '@jadawel/modules/builder/pathParamTypes'

import {
  PreviewPageActionType,
  PublishPageActionType,
} from '@jadawel/modules/builder/pageActionTypes'

import {
  PageParameterDataProviderType,
  DataSourceDataProviderType,
  CurrentRecordDataProviderType,
  FormDataProviderType,
  PreviousActionDataProviderType,
  UserDataProviderType,
  DataSourceContextDataProviderType,
} from '@jadawel/modules/builder/dataProviderTypes'

import {
  ColorThemeConfigBlockType,
  TypographyThemeConfigBlockType,
  ButtonThemeConfigBlockType,
  LinkThemeConfigBlockType,
  ImageThemeConfigBlockType,
  PageThemeConfigBlockType,
  InputThemeConfigBlockType,
  TableThemeConfigBlockType,
} from '@jadawel/modules/builder/themeConfigBlockTypes'
import {
  CreateRowWorkflowActionType,
  NotificationWorkflowActionType,
  OpenPageWorkflowActionType,
  UpdateRowWorkflowActionType,
  LogoutWorkflowActionType,
  RefreshDataSourceWorkflowActionType,
  DeleteRowWorkflowActionType,
  CoreHTTPRequestWorkflowActionType,
  CoreSMTPEmailWorkflowActionType,
  AIAgentWorkflowActionType,
  SlackWriteMessageWorkflowActionType,
} from '@jadawel/modules/builder/workflowActionTypes'

import {
  BooleanCollectionFieldType,
  TextCollectionFieldType,
  LinkCollectionFieldType,
  ButtonCollectionFieldType,
  TagsCollectionFieldType,
  ImageCollectionFieldType,
  RatingCollectionFieldType,
} from '@jadawel/modules/builder/collectionFieldTypes'

import {
  InterFontFamilyType,
  ArialFontFamilyType,
  VerdanaFontFamilyType,
  TahomaFontFamilyType,
  TrebuchetMSFontFamilyType,
  TimesNewRomanFontFamilyType,
  GeorgiaFontFamilyType,
  GaramondFontFamilyType,
  CourierNewFontFamilyType,
  BrushScriptMTFontFamilyType,
} from '@jadawel/modules/builder/fontFamilyTypes'
import {
  TextQueryParamType,
  NumericQueryParamType,
} from '@jadawel/modules/builder/queryParamTypes'
import { BuilderGuidedTourType } from '@jadawel/modules/builder/guidedTourTypes'
import { BuilderSearchType } from '@jadawel/modules/builder/searchTypes'
import { searchTypeRegistry } from '@jadawel/modules/core/search/types/registry'

export default defineNuxtPlugin({
  name: 'builder',
  dependsOn: ['core', 'store'],
  async setup(nuxtApp) {
    const { $store, $registry, $clientErrorMap, $i18n } = nuxtApp
    const context = { app: nuxtApp }

    $clientErrorMap.setError(
      'ERROR_PAGE_NAME_NOT_UNIQUE',
      $i18n.t('pageErrors.errorNameNotUnique'),
      $i18n.t('pageErrors.errorNameNotUniqueDescription')
    )

    $store.registerModuleNuxtSafe('page', pageStore)
    $store.registerModuleNuxtSafe('element', elementStore)
    $store.registerModuleNuxtSafe('domain', domainStore)
    $store.registerModuleNuxtSafe('publicBuilder', publicBuilderStore)
    $store.registerModuleNuxtSafe('dataSource', dataSourceStore)
    $store.registerModuleNuxtSafe('pageParameter', pageParameterStore)
    $store.registerModuleNuxtSafe('dataSourceContent', dataSourceContentStore)
    $store.registerModuleNuxtSafe('elementContent', elementContentStore)
    $store.registerModuleNuxtSafe('theme', themeStore)
    $store.registerModuleNuxtSafe(
      'builderWorkflowAction',
      builderWorkflowActionStore
    )
    $store.registerModuleNuxtSafe('formData', formDataStore)
    $store.registerModuleNuxtSafe('builderToast', builderToast)

    $registry.registerNamespace('builderSettings')
    $registry.registerNamespace('element')
    $registry.registerNamespace('device')
    $registry.registerNamespace('pageHeaderItem')
    $registry.registerNamespace('domain')
    $registry.registerNamespace('pageSettings')
    $registry.registerNamespace('pathParamType')
    $registry.registerNamespace('builderDataProvider')
    $registry.registerNamespace('themeConfigBlock')
    $registry.registerNamespace('fontFamily')
    $registry.registerNamespace('builderPageDecorator')
    $registry.registerNamespace('pageSidePanel')
    $registry.registerNamespace('queryParamType')
    $registry.registerNamespace('pageAction')
    $registry.registerNamespace('collectionField')

    $registry.register('application', new BuilderApplicationType(context))
    $registry.register(
      'lastViewedItem',
      new BuilderPageLastViewedItemType(context)
    )
    $registry.register('job', new DuplicatePageJobType(context))
    $registry.register('job', new PublishBuilderJobType(context))

    $registry.register(
      'builderSettings',
      new GeneralBuilderSettingsType(context)
    )
    $registry.register(
      'builderSettings',
      new IntegrationsBuilderSettingsType(context)
    )
    $registry.register('builderSettings', new ThemeBuilderSettingsType(context))
    $registry.register(
      'builderSettings',
      new DomainsBuilderSettingsType(context)
    )

    $registry.register(
      'builderSettings',
      new UserSourcesBuilderSettingsType(context)
    )

    $registry.register('errorPage', new PublicSiteErrorPageType(context))

    $registry.register('element', new HeadingElementType(context))
    $registry.register('element', new TextElementType(context))
    $registry.register('element', new ImageElementType(context))
    $registry.register('element', new IFrameElementType(context))
    $registry.register('element', new LinkElementType(context))
    $registry.register('element', new ButtonElementType(context))
    $registry.register('element', new RatingElementType(context))
    $registry.register('element', new TableElementType(context))
    $registry.register('element', new SimpleContainerElementType(context))
    $registry.register('element', new ColumnElementType(context))
    $registry.register('element', new HeaderElementType(context))
    $registry.register('element', new FooterElementType(context))
    $registry.register('element', new FormContainerElementType(context))
    $registry.register('element', new InputTextElementType(context))
    $registry.register('element', new ChoiceElementType(context))
    $registry.register('element', new CheckboxElementType(context))
    $registry.register('element', new DateTimePickerElementType(context))
    $registry.register('element', new RecordSelectorElementType(context))
    $registry.register('element', new RepeatElementType(context))
    $registry.register('element', new RatingInputElementType(context))
    $registry.register('element', new MenuElementType(context))

    $registry.register('device', new DesktopDeviceType(context))
    $registry.register('device', new TabletDeviceType(context))
    $registry.register('device', new SmartphoneDeviceType(context))

    $registry.register(
      'pageHeaderItem',
      new ElementsPageHeaderItemType(context)
    )
    $registry.register(
      'pageHeaderItem',
      new DataSourcesPageHeaderItemType(context)
    )
    $registry.register(
      'pageHeaderItem',
      new SettingsPageHeaderItemType(context)
    )
    $registry.register('pageSidePanel', new GeneralPageSidePanelType(context))
    $registry.register('pageSidePanel', new StylePageSidePanelType(context))
    $registry.register(
      'pageSidePanel',
      new VisibilityPageSidePanelType(context)
    )
    $registry.register('pageSidePanel', new EventsPageSidePanelType(context))

    $registry.register('domain', new CustomDomainType(context))
    $registry.register('domain', new SubDomainType(context))

    $registry.register('pageSettings', new PagePageSettingsType(context))
    $registry.register('pageSettings', new PageVisibilitySettingsType(context))

    $registry.register('pathParamType', new TextPathParamType(context))
    $registry.register('pathParamType', new NumericPathParamType(context))

    $registry.register('queryParamType', new TextQueryParamType(context))
    $registry.register('queryParamType', new NumericQueryParamType(context))

    $registry.register('pageAction', new PublishPageActionType(context))
    $registry.register('pageAction', new PreviewPageActionType(context))

    $registry.register('builderDataProvider', new UserDataProviderType(context))
    $registry.register(
      'builderDataProvider',
      new CurrentRecordDataProviderType(context)
    )
    $registry.register(
      'builderDataProvider',
      new DataSourceDataProviderType(context)
    )
    $registry.register(
      'builderDataProvider',
      new DataSourceContextDataProviderType(context)
    )
    $registry.register(
      'builderDataProvider',
      new PageParameterDataProviderType(context)
    )
    $registry.register('builderDataProvider', new FormDataProviderType(context))
    $registry.register(
      'builderDataProvider',
      new PreviousActionDataProviderType(context)
    )
    $registry.register(
      'themeConfigBlock',
      new ColorThemeConfigBlockType(context)
    )
    $registry.register(
      'themeConfigBlock',
      new TypographyThemeConfigBlockType(context)
    )
    $registry.register(
      'themeConfigBlock',
      new ButtonThemeConfigBlockType(context)
    )
    $registry.register(
      'themeConfigBlock',
      new LinkThemeConfigBlockType(context)
    )
    $registry.register(
      'themeConfigBlock',
      new ImageThemeConfigBlockType(context)
    )
    $registry.register(
      'themeConfigBlock',
      new PageThemeConfigBlockType(context)
    )
    $registry.register(
      'themeConfigBlock',
      new InputThemeConfigBlockType(context)
    )
    $registry.register(
      'themeConfigBlock',
      new TableThemeConfigBlockType(context)
    )

    $registry.register(
      'workflowAction',
      new NotificationWorkflowActionType(context)
    )
    $registry.register(
      'workflowAction',
      new OpenPageWorkflowActionType(context)
    )
    $registry.register('workflowAction', new LogoutWorkflowActionType(context))
    $registry.register(
      'workflowAction',
      new RefreshDataSourceWorkflowActionType(context)
    )
    $registry.register(
      'workflowAction',
      new CoreHTTPRequestWorkflowActionType(context)
    )
    $registry.register(
      'workflowAction',
      new CoreSMTPEmailWorkflowActionType(context)
    )
    $registry.register('workflowAction', new AIAgentWorkflowActionType(context))
    $registry.register(
      'workflowAction',
      new CreateRowWorkflowActionType(context)
    )
    $registry.register(
      'workflowAction',
      new UpdateRowWorkflowActionType(context)
    )
    $registry.register(
      'workflowAction',
      new DeleteRowWorkflowActionType(context)
    )
    $registry.register(
      'workflowAction',
      new SlackWriteMessageWorkflowActionType(context)
    )

    $registry.register(
      'collectionField',
      new BooleanCollectionFieldType(context)
    )
    $registry.register('collectionField', new TextCollectionFieldType(context))
    $registry.register('collectionField', new LinkCollectionFieldType(context))
    $registry.register('collectionField', new TagsCollectionFieldType(context))
    $registry.register(
      'collectionField',
      new ButtonCollectionFieldType(context)
    )
    $registry.register('collectionField', new ImageCollectionFieldType(context))
    $registry.register(
      'collectionField',
      new RatingCollectionFieldType(context)
    )

    $registry.register('fontFamily', new InterFontFamilyType(context))
    $registry.register('fontFamily', new ArialFontFamilyType(context))
    $registry.register('fontFamily', new VerdanaFontFamilyType(context))
    $registry.register('fontFamily', new TahomaFontFamilyType(context))
    $registry.register('fontFamily', new TrebuchetMSFontFamilyType(context))
    $registry.register('fontFamily', new TimesNewRomanFontFamilyType(context))
    $registry.register('fontFamily', new GeorgiaFontFamilyType(context))
    $registry.register('fontFamily', new GaramondFontFamilyType(context))
    $registry.register('fontFamily', new CourierNewFontFamilyType(context))
    $registry.register('fontFamily', new BrushScriptMTFontFamilyType(context))

    $registry.register('guidedTour', new BuilderGuidedTourType(context))

    searchTypeRegistry.register(new BuilderSearchType(context))
  },
})
