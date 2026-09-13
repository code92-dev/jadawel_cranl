import { defineNuxtPlugin } from '#app'
import { DatabaseApplicationType } from '@jadawel/modules/database/applicationTypes'
import {
  DuplicateTableJobType,
  SyncDataSyncTableJobType,
  FileImportJobType,
  DuplicateFieldJobType,
  AirtableJobType,
} from '@jadawel/modules/database/jobTypes'
import {
  GridViewType,
  GalleryViewType,
  FormViewType,
} from '@jadawel/modules/database/viewTypes'
import {
  TextFieldType,
  LongTextFieldType,
  URLFieldType,
  EmailFieldType,
  LinkRowFieldType,
  NumberFieldType,
  RatingFieldType,
  BooleanFieldType,
  DateFieldType,
  LastModifiedFieldType,
  LastModifiedByFieldType,
  FileFieldType,
  SingleSelectFieldType,
  MultipleSelectFieldType,
  PhoneNumberFieldType,
  CreatedOnFieldType,
  CreatedByFieldType,
  DurationFieldType,
  FormulaFieldType,
  CountFieldType,
  RollupFieldType,
  LookupFieldType,
  MultipleCollaboratorsFieldType,
  UUIDFieldType,
  AutonumberFieldType,
  PasswordFieldType,
  FormViewEditRowFieldType,
} from '@jadawel/modules/database/fieldTypes'
import {
  EqualViewFilterType,
  NotEqualViewFilterType,
  ContainsViewFilterType,
  FilenameContainsViewFilterType,
  FilesLowerThanViewFilterType,
  HasFileTypeViewFilterType,
  ContainsNotViewFilterType,
  LengthIsLowerThanViewFilterType,
  HigherThanViewFilterType,
  HigherThanOrEqualViewFilterType,
  LowerThanViewFilterType,
  LowerThanOrEqualViewFilterType,
  IsEvenAndWholeViewFilterType,
  SingleSelectEqualViewFilterType,
  SingleSelectNotEqualViewFilterType,
  SingleSelectIsAnyOfViewFilterType,
  SingleSelectIsNoneOfViewFilterType,
  BooleanViewFilterType,
  EmptyViewFilterType,
  NotEmptyViewFilterType,
  LinkRowHasFilterType,
  LinkRowHasNotFilterType,
  MultipleSelectHasFilterType,
  MultipleSelectHasNotFilterType,
  MultipleCollaboratorsHasFilterType,
  MultipleCollaboratorsHasNotFilterType,
  LinkRowContainsFilterType,
  LinkRowNotContainsFilterType,
  ContainsWordViewFilterType,
  DoesntContainWordViewFilterType,
  UserIsFilterType,
  UserIsNotFilterType,
  DateIsEqualMultiStepViewFilterType,
  DateIsBeforeMultiStepViewFilterType,
  DateIsOnOrBeforeMultiStepViewFilterType,
  DateIsAfterMultiStepViewFilterType,
  DateIsOnOrAfterMultiStepViewFilterType,
  DateIsWithinMultiStepViewFilterType,
  DateIsNotEqualMultiStepViewFilterType,
  // Deprecated date filter types
  DateEqualViewFilterType,
  DateNotEqualViewFilterType,
  DateEqualsTodayViewFilterType,
  DateBeforeTodayViewFilterType,
  DateAfterTodayViewFilterType,
  DateWithinDaysViewFilterType,
  DateWithinWeeksViewFilterType,
  DateWithinMonthsViewFilterType,
  DateEqualsDaysAgoViewFilterType,
  DateEqualsMonthsAgoViewFilterType,
  DateEqualsYearsAgoViewFilterType,
  DateEqualsCurrentWeekViewFilterType,
  DateEqualsCurrentMonthViewFilterType,
  DateEqualsCurrentYearViewFilterType,
  DateBeforeViewFilterType,
  DateBeforeOrEqualViewFilterType,
  DateAfterDaysAgoViewFilterType,
  DateAfterViewFilterType,
  DateAfterOrEqualViewFilterType,
  DateEqualsDayOfMonthViewFilterType,
} from '@jadawel/modules/database/viewFilters'
import {
  HasValueEqualViewFilterType,
  HasEmptyValueViewFilterType,
  HasNotEmptyValueViewFilterType,
  HasNotValueEqualViewFilterType,
  HasValueContainsViewFilterType,
  HasNotValueContainsViewFilterType,
  HasValueContainsWordViewFilterType,
  HasNotValueContainsWordViewFilterType,
  HasValueLengthIsLowerThanViewFilterType,
  HasAllValuesEqualViewFilterType,
  HasAnySelectOptionEqualViewFilterType,
  HasNoneSelectOptionEqualViewFilterType,
  HasValueLowerThanViewFilterType,
  HasValueLowerThanOrEqualViewFilterType,
  HasValueHigherThanViewFilterType,
  HasValueHigherThanOrEqualViewFilterType,
  HasNotValueLowerThanOrEqualViewFilterType,
  HasNotValueLowerThanViewFilterType,
  HasNotValueHigherThanOrEqualViewFilterType,
  HasNotValueHigherThanViewFilterType,
  HasDateEqualViewFilterType,
  HasNotDateEqualViewFilterType,
  HasDateBeforeViewFilterType,
  HasNotDateBeforeViewFilterType,
  HasDateOnOrBeforeViewFilterType,
  HasNotDateOnOrBeforeViewFilterType,
  HasDateAfterViewFilterType,
  HasNotDateAfterViewFilterType,
  HasDateOnOrAfterViewFilterType,
  HasNotDateOnOrAfterViewFilterType,
  HasDateWithinViewFilterType,
  HasNotDateWithinViewFilterType,
} from '@jadawel/modules/database/arrayViewFilters'
import {
  CSVImporterType,
  PasteImporterType,
  XMLImporterType,
  JSONImporterType,
  ExcelImporterType,
} from '@jadawel/modules/database/importerTypes'
import {
  ICalCalendarDataSyncType,
  PostgreSQLDataSyncType,
} from '@jadawel/modules/database/dataSyncTypes'
import {
  RowsCreatedWebhookEventType,
  RowsUpdatedWebhookEventType,
  RowsDeletedWebhookEventType,
  FieldCreatedWebhookEventType,
  FieldUpdatedWebhookEventType,
  FieldDeletedWebhookEventType,
  ViewCreatedWebhookEventType,
  ViewUpdatedWebhookEventType,
  ViewDeletedWebhookEventType,
} from '@jadawel/modules/database/webhookEventTypes'
import {
  ImageFilePreview,
  AudioFilePreview,
  VideoFilePreview,
  PDFBrowserFilePreview,
  GoogleDocFilePreview,
} from '@jadawel/modules/database/filePreviewTypes'

import {
  TextTypeUniqueWithEmptyConstraintType,
  RatingTypeUniqueWithEmptyConstraintType,
  GenericUniqueWithEmptyConstraintType,
} from '@jadawel/modules/database/fieldConstraintTypes'

import { APITokenSettingsType } from '@jadawel/modules/database/settingsTypes'

import { CSVTableExporterType } from '@jadawel/modules/database/exporterTypes'
import {
  JadawelAdd,
  JadawelAnd,
  JadawelConcat,
  JadawelDateDiff,
  JadawelDateInterval,
  JadawelDatetimeFormat,
  JadawelDatetimeFormatTz,
  JadawelDay,
  JadawelDivide,
  JadawelEncodeUri,
  JadawelEncodeUriComponent,
  JadawelEqual,
  JadawelHasOption,
  JadawelField,
  JadawelSearch,
  JadawelGreaterThan,
  JadawelGreaterThanOrEqual,
  JadawelIf,
  JadawelIsBlank,
  JadawelIsNull,
  JadawelDurationToSeconds,
  JadawelSecondsToDuration,
  JadawelLessThan,
  JadawelLessThanOrEqual,
  JadawelLower,
  JadawelSplitPart,
  JadawelMinus,
  JadawelMultiply,
  JadawelNot,
  JadawelOr,
  JadawelReplace,
  JadawelRowId,
  JadawelT,
  JadawelNow,
  JadawelToday,
  JadawelToDateTz,
  JadawelToDate,
  JadawelToNumber,
  JadawelToText,
  JadawelUpper,
  JadawelReverse,
  JadawelLength,
  JadawelNotEqual,
  JadawelLookup,
  JadawelSum,
  JadawelAvg,
  JadawelVariancePop,
  JadawelVarianceSample,
  JadawelStddevSample,
  JadawelStddevPop,
  JadawelJoin,
  JadawelCount,
  JadawelMin,
  JadawelMax,
  JadawelEvery,
  JadawelAny,
  JadawelWhenEmpty,
  JadawelSecond,
  JadawelYear,
  JadawelMonth,
  JadawelLeast,
  JadawelGreatest,
  JadawelRegexReplace,
  JadawelLink,
  JadawelTrim,
  JadawelRight,
  JadawelLeft,
  JadawelContains,
  JadawelFilter,
  JadawelTrunc,
  JadawelIsNaN,
  JadawelWhenNaN,
  JadawelEven,
  JadawelOdd,
  JadawelCeil,
  JadawelFloor,
  JadawelAbs,
  JadawelExp,
  JadawelLn,
  JadawelSign,
  JadawelSqrt,
  JadawelRound,
  JadawelLog,
  JadawelPower,
  JadawelMod,
  JadawelButton,
  JadawelGetLinkUrl,
  JadawelGetLinkLabel,
  JadawelIsImage,
  JadawelGetImageHeight,
  JadawelGetImageWidth,
  JadawelGetFileSize,
  JadawelGetFileMimeType,
  JadawelGetFileVisibleName,
  JadawelIndex,
  JadawelGetFileCount,
  JadawelToUrl,
  JadawelArrayUnique,
  JadawelArraySlice,
  JadawelFirst,
  JadawelLast,
} from '@jadawel/modules/database/formula/functions'
import {
  JadawelFormulaArrayType,
  JadawelFormulaBooleanType,
  JadawelFormulaButtonType,
  JadawelFormulaCharType,
  JadawelFormulaLinkType,
  JadawelFormulaDateIntervalType, // Deprecated
  JadawelFormulaDurationType,
  JadawelFormulaDateType,
  JadawelFormulaInvalidType,
  JadawelFormulaNumberType,
  JadawelFormulaSingleSelectType,
  JadawelFormulaMultipleSelectType,
  JadawelFormulaMultipleCollaboratorsType,
  JadawelFormulaSpecialType,
  JadawelFormulaTextType,
  JadawelFormulaFileType,
  JadawelFormulaURLType,
} from '@jadawel/modules/database/formula/formulaTypes'
import {
  CountViewAggregationType,
  EmptyCountViewAggregationType,
  NotEmptyCountViewAggregationType,
  CheckedCountViewAggregationType,
  NotCheckedCountViewAggregationType,
  EmptyPercentageViewAggregationType,
  NotEmptyPercentageViewAggregationType,
  CheckedPercentageViewAggregationType,
  NotCheckedPercentageViewAggregationType,
  UniqueCountViewAggregationType,
  MinViewAggregationType,
  MaxViewAggregationType,
  EarliestDateViewAggregationType,
  LatestDateViewAggregationType,
  SumViewAggregationType,
  AverageViewAggregationType,
  StdDevViewAggregationType,
  VarianceViewAggregationType,
  MedianViewAggregationType,
  DistributionViewAggregationType,
} from '@jadawel/modules/database/viewAggregationTypes'
import { FormViewFormModeType } from '@jadawel/modules/database/formViewModeTypes'
import { CollaborativeViewOwnershipType } from '@jadawel/modules/database/viewOwnershipTypes'
import { DatabasePlugin } from '@jadawel/modules/database/plugins'
import {
  CollaboratorAddedToRowNotificationType,
  FormSubmittedNotificationType,
  UserMentionInRichTextFieldNotificationType,
  WebhookDeactivatedNotificationType,
  WebhookPayloadTooLargedNotificationType,
} from '@jadawel/modules/database/notificationTypes'
import { HistoryRowModalSidebarType } from '@jadawel/modules/database/rowModalSidebarTypes'
import { FieldsDataProviderType } from '@jadawel/modules/database/dataProviderTypes'

import {
  DatabaseOnboardingType,
  DatabaseScratchTrackOnboardingType,
  DatabaseImportOnboardingType,
  DatabaseScratchTrackFieldsOnboardingType,
} from '@jadawel/modules/database/onboardingTypes'

import {
  ScratchDatabaseOnboardingStepType,
  ImportDatabaseOnboardingStepType,
  AirtableDatabaseOnboardingStepType,
  TemplateDatabaseOnboardingStepType,
} from '@jadawel/modules/database/databaseOnboardingStepTypes'

import {
  DatabaseScratchTrackCampaignFieldsOnboardingType,
  DatabaseScratchTrackCustomFieldsOnboardingType,
  DatabaseScratchTrackProjectFieldsOnboardingType,
  DatabaseScratchTrackTaskFieldsOnboardingType,
  DatabaseScratchTrackTeamFieldsOnboardingType,
} from '@jadawel/modules/database/databaseScratchTrackFieldsStepType'
import {
  SyncedFieldsConfigureDataSyncType,
  SettingsConfigureDataSyncType,
} from '@jadawel/modules/database/configureDataSyncTypes'
import { DatabaseGuidedTourType } from '@jadawel/modules/database/guidedTourTypes'
import {
  DatabaseSearchType,
  DatabaseTableSearchType,
  DatabaseFieldSearchType,
  DatabaseRowSearchType,
} from '@jadawel/modules/database/searchTypes'
import { searchTypeRegistry } from '@jadawel/modules/core/search/types/registry'

export default defineNuxtPlugin({
  name: 'database',
  dependsOn: ['core'],
  setup(nuxtApp) {
    const { $registry } = nuxtApp

    const context = { app: nuxtApp }

    $registry.registerNamespace('viewDecorator')
    $registry.registerNamespace('decoratorValueProvider')
    $registry.registerNamespace('twoWaySyncStrategy')
    $registry.registerNamespace('viewFilter')
    $registry.registerNamespace('viewOwnershipType')
    $registry.registerNamespace('fieldConstraint')
    $registry.registerNamespace('importer')
    $registry.registerNamespace('exporter')
    $registry.registerNamespace('dataSync')
    $registry.registerNamespace('webhookEvent')
    $registry.registerNamespace('formula_function')
    $registry.registerNamespace('formula_type')
    $registry.registerNamespace('preview')
    $registry.registerNamespace('viewAggregation')
    $registry.registerNamespace('formViewMode')
    $registry.registerNamespace('databaseDataProvider')
    $registry.registerNamespace('rowModalSidebar')
    $registry.registerNamespace('onboardingTrackFields')
    $registry.registerNamespace('configureDataSync')
    $registry.registerNamespace('databaseOnboardingStep')

    $registry.register('plugin', new DatabasePlugin(context))
    $registry.register('application', new DatabaseApplicationType(context))

    $registry.register('job', new DuplicateTableJobType(context))
    $registry.register('job', new SyncDataSyncTableJobType(context))
    $registry.register('job', new FileImportJobType(context))
    $registry.register('job', new DuplicateFieldJobType(context))
    $registry.register('job', new AirtableJobType(context))

    $registry.register('view', new GridViewType(context))
    $registry.register('view', new GalleryViewType(context))
    $registry.register('view', new FormViewType(context))
    $registry.register('viewFilter', new EqualViewFilterType(context))
    $registry.register('viewFilter', new NotEqualViewFilterType(context))
    $registry.register(
      'viewFilter',
      new DateIsEqualMultiStepViewFilterType(context)
    )
    $registry.register(
      'viewFilter',
      new DateIsNotEqualMultiStepViewFilterType(context)
    )
    $registry.register(
      'viewFilter',
      new DateIsBeforeMultiStepViewFilterType(context)
    )
    $registry.register(
      'viewFilter',
      new DateIsOnOrBeforeMultiStepViewFilterType(context)
    )
    $registry.register(
      'viewFilter',
      new DateIsAfterMultiStepViewFilterType(context)
    )
    $registry.register(
      'viewFilter',
      new DateIsOnOrAfterMultiStepViewFilterType(context)
    )
    $registry.register(
      'viewFilter',
      new DateIsWithinMultiStepViewFilterType(context)
    )
    // DEPRECATED
    $registry.register('viewFilter', new DateEqualViewFilterType(context))
    $registry.register('viewFilter', new DateNotEqualViewFilterType(context))
    $registry.register('viewFilter', new DateEqualsTodayViewFilterType(context))
    $registry.register('viewFilter', new DateBeforeTodayViewFilterType(context))
    $registry.register('viewFilter', new DateAfterTodayViewFilterType(context))
    $registry.register('viewFilter', new DateWithinDaysViewFilterType(context))
    $registry.register('viewFilter', new DateWithinWeeksViewFilterType(context))
    $registry.register(
      'viewFilter',
      new DateWithinMonthsViewFilterType(context)
    )
    $registry.register(
      'viewFilter',
      new DateEqualsDaysAgoViewFilterType(context)
    )
    $registry.register(
      'viewFilter',
      new DateEqualsMonthsAgoViewFilterType(context)
    )
    $registry.register(
      'viewFilter',
      new DateEqualsYearsAgoViewFilterType(context)
    )
    $registry.register(
      'viewFilter',
      new DateEqualsCurrentWeekViewFilterType(context)
    )
    $registry.register(
      'viewFilter',
      new DateEqualsCurrentMonthViewFilterType(context)
    )
    $registry.register(
      'viewFilter',
      new DateEqualsCurrentYearViewFilterType(context)
    )
    $registry.register(
      'viewFilter',
      new DateEqualsDayOfMonthViewFilterType(context)
    )
    $registry.register('viewFilter', new DateBeforeViewFilterType(context))
    $registry.register(
      'viewFilter',
      new DateBeforeOrEqualViewFilterType(context)
    )
    $registry.register('viewFilter', new DateAfterViewFilterType(context))
    $registry.register(
      'viewFilter',
      new DateAfterOrEqualViewFilterType(context)
    )
    $registry.register(
      'viewFilter',
      new DateAfterDaysAgoViewFilterType(context)
    )
    // END
    $registry.register('viewFilter', new HasEmptyValueViewFilterType(context))
    $registry.register(
      'viewFilter',
      new HasNotEmptyValueViewFilterType(context)
    )
    $registry.register('viewFilter', new HasValueEqualViewFilterType(context))
    $registry.register(
      'viewFilter',
      new HasNotValueEqualViewFilterType(context)
    )
    $registry.register(
      'viewFilter',
      new HasValueContainsViewFilterType(context)
    )
    $registry.register(
      'viewFilter',
      new HasNotValueContainsViewFilterType(context)
    )
    $registry.register(
      'viewFilter',
      new HasValueContainsWordViewFilterType(context)
    )
    $registry.register(
      'viewFilter',
      new HasNotValueContainsWordViewFilterType(context)
    )
    $registry.register(
      'viewFilter',
      new HasValueLengthIsLowerThanViewFilterType(context)
    )
    $registry.register(
      'viewFilter',

      new HasAllValuesEqualViewFilterType(context)
    )
    $registry.register(
      'viewFilter',
      new HasAnySelectOptionEqualViewFilterType(context)
    )
    $registry.register(
      'viewFilter',
      new HasNoneSelectOptionEqualViewFilterType(context)
    )
    $registry.register('viewFilter', new ContainsViewFilterType(context))
    $registry.register('viewFilter', new ContainsNotViewFilterType(context))
    $registry.register('viewFilter', new ContainsWordViewFilterType(context))
    $registry.register(
      'viewFilter',
      new DoesntContainWordViewFilterType(context)
    )
    $registry.register(
      'viewFilter',
      new FilenameContainsViewFilterType(context)
    )
    $registry.register('viewFilter', new HasFileTypeViewFilterType(context))
    $registry.register('viewFilter', new FilesLowerThanViewFilterType(context))
    $registry.register(
      'viewFilter',
      new LengthIsLowerThanViewFilterType(context)
    )
    $registry.register('viewFilter', new HigherThanViewFilterType(context))
    $registry.register(
      'viewFilter',
      new HigherThanOrEqualViewFilterType(context)
    )
    $registry.register('viewFilter', new LowerThanViewFilterType(context))
    $registry.register(
      'viewFilter',
      new LowerThanOrEqualViewFilterType(context)
    )
    $registry.register('viewFilter', new IsEvenAndWholeViewFilterType(context))
    $registry.register(
      'viewFilter',
      new SingleSelectEqualViewFilterType(context)
    )
    $registry.register(
      'viewFilter',
      new SingleSelectNotEqualViewFilterType(context)
    )
    $registry.register(
      'viewFilter',
      new SingleSelectIsAnyOfViewFilterType(context)
    )
    $registry.register(
      'viewFilter',
      new SingleSelectIsNoneOfViewFilterType(context)
    )

    $registry.register('viewFilter', new BooleanViewFilterType(context))
    $registry.register('viewFilter', new LinkRowHasFilterType(context))
    $registry.register('viewFilter', new LinkRowHasNotFilterType(context))
    $registry.register('viewFilter', new LinkRowContainsFilterType(context))
    $registry.register('viewFilter', new LinkRowNotContainsFilterType(context))
    $registry.register('viewFilter', new MultipleSelectHasFilterType(context))
    $registry.register(
      'viewFilter',
      new MultipleSelectHasNotFilterType(context)
    )
    $registry.register(
      'viewFilter',
      new MultipleCollaboratorsHasFilterType(context)
    )
    $registry.register(
      'viewFilter',
      new MultipleCollaboratorsHasNotFilterType(context)
    )
    $registry.register('viewFilter', new EmptyViewFilterType(context))
    $registry.register('viewFilter', new NotEmptyViewFilterType(context))
    $registry.register('viewFilter', new UserIsFilterType(context))
    $registry.register('viewFilter', new UserIsNotFilterType(context))
    $registry.register(
      'viewFilter',
      new HasValueHigherThanViewFilterType(context)
    )
    $registry.register(
      'viewFilter',
      new HasNotValueHigherThanViewFilterType(context)
    )
    $registry.register(
      'viewFilter',
      new HasValueHigherThanOrEqualViewFilterType(context)
    )
    $registry.register(
      'viewFilter',
      new HasNotValueHigherThanOrEqualViewFilterType(context)
    )
    $registry.register(
      'viewFilter',
      new HasValueLowerThanViewFilterType(context)
    )
    $registry.register(
      'viewFilter',
      new HasNotValueLowerThanViewFilterType(context)
    )
    $registry.register(
      'viewFilter',
      new HasValueLowerThanOrEqualViewFilterType(context)
    )
    $registry.register(
      'viewFilter',
      new HasNotValueLowerThanOrEqualViewFilterType(context)
    )
    $registry.register('viewFilter', new HasDateEqualViewFilterType(context))
    $registry.register('viewFilter', new HasNotDateEqualViewFilterType(context))
    $registry.register('viewFilter', new HasDateBeforeViewFilterType(context))
    $registry.register(
      'viewFilter',
      new HasNotDateBeforeViewFilterType(context)
    )
    $registry.register(
      'viewFilter',
      new HasDateOnOrBeforeViewFilterType(context)
    )
    $registry.register(
      'viewFilter',
      new HasNotDateOnOrBeforeViewFilterType(context)
    )
    $registry.register('viewFilter', new HasDateAfterViewFilterType(context))
    $registry.register('viewFilter', new HasNotDateAfterViewFilterType(context))
    $registry.register(
      'viewFilter',
      new HasDateOnOrAfterViewFilterType(context)
    )
    $registry.register(
      'viewFilter',
      new HasNotDateOnOrAfterViewFilterType(context)
    )
    $registry.register('viewFilter', new HasDateWithinViewFilterType(context))
    $registry.register(
      'viewFilter',
      new HasNotDateWithinViewFilterType(context)
    )

    $registry.register(
      'viewOwnershipType',
      new CollaborativeViewOwnershipType(context)
    )

    $registry.register('field', new TextFieldType(context))
    $registry.register('field', new LongTextFieldType(context))
    $registry.register('field', new LinkRowFieldType(context))
    $registry.register('field', new NumberFieldType(context))
    $registry.register('field', new RatingFieldType(context))
    $registry.register('field', new BooleanFieldType(context))
    $registry.register('field', new DateFieldType(context))
    $registry.register('field', new LastModifiedFieldType(context))
    $registry.register('field', new LastModifiedByFieldType(context))
    $registry.register('field', new CreatedOnFieldType(context))
    $registry.register('field', new CreatedByFieldType(context))
    $registry.register('field', new DurationFieldType(context))
    $registry.register('field', new URLFieldType(context))
    $registry.register('field', new EmailFieldType(context))
    $registry.register('field', new FileFieldType(context))
    $registry.register('field', new SingleSelectFieldType(context))
    $registry.register('field', new MultipleSelectFieldType(context))
    $registry.register('field', new PhoneNumberFieldType(context))
    $registry.register('field', new FormulaFieldType(context))
    $registry.register('field', new CountFieldType(context))
    $registry.register('field', new RollupFieldType(context))
    $registry.register('field', new LookupFieldType(context))
    $registry.register('field', new MultipleCollaboratorsFieldType(context))
    $registry.register('field', new UUIDFieldType(context))
    $registry.register('field', new AutonumberFieldType(context))
    $registry.register('field', new PasswordFieldType(context))
    $registry.register('field', new FormViewEditRowFieldType(context))

    $registry.register(
      'fieldConstraint',
      new TextTypeUniqueWithEmptyConstraintType(context)
    )
    $registry.register(
      'fieldConstraint',
      new RatingTypeUniqueWithEmptyConstraintType(context)
    )
    $registry.register(
      'fieldConstraint',
      new GenericUniqueWithEmptyConstraintType(context)
    )

    $registry.register('importer', new CSVImporterType(context))
    $registry.register('importer', new PasteImporterType(context))
    $registry.register('importer', new XMLImporterType(context))
    $registry.register('importer', new JSONImporterType(context))
    $registry.register('importer', new ExcelImporterType(context))
    $registry.register('dataSync', new ICalCalendarDataSyncType(context))
    $registry.register('dataSync', new PostgreSQLDataSyncType(context))
    $registry.register('settings', new APITokenSettingsType(context))
    $registry.register('exporter', new CSVTableExporterType(context))
    $registry.register('webhookEvent', new RowsCreatedWebhookEventType(context))
    $registry.register('webhookEvent', new RowsUpdatedWebhookEventType(context))
    $registry.register('webhookEvent', new RowsDeletedWebhookEventType(context))
    $registry.register(
      'webhookEvent',
      new FieldCreatedWebhookEventType(context)
    )
    $registry.register(
      'webhookEvent',
      new FieldUpdatedWebhookEventType(context)
    )
    $registry.register(
      'webhookEvent',
      new FieldDeletedWebhookEventType(context)
    )
    $registry.register('webhookEvent', new ViewCreatedWebhookEventType(context))
    $registry.register('webhookEvent', new ViewUpdatedWebhookEventType(context))
    $registry.register('webhookEvent', new ViewDeletedWebhookEventType(context))

    // Text functions
    $registry.register('formula_function', new JadawelUpper(context))
    $registry.register('formula_function', new JadawelLower(context))
    $registry.register('formula_function', new JadawelConcat(context))
    $registry.register('formula_function', new JadawelToText(context))
    $registry.register('formula_function', new JadawelT(context))
    $registry.register('formula_function', new JadawelReplace(context))
    $registry.register('formula_function', new JadawelSearch(context))
    $registry.register('formula_function', new JadawelLength(context))
    $registry.register('formula_function', new JadawelReverse(context))
    $registry.register('formula_function', new JadawelEncodeUri(context))
    $registry.register(
      'formula_function',
      new JadawelEncodeUriComponent(context)
    )
    $registry.register('formula_function', new JadawelSplitPart(context))
    // Number functions
    $registry.register('formula_function', new JadawelMultiply(context))
    $registry.register('formula_function', new JadawelDivide(context))
    $registry.register('formula_function', new JadawelToNumber(context))
    // Boolean functions
    $registry.register('formula_function', new JadawelIf(context))
    $registry.register('formula_function', new JadawelEqual(context))
    $registry.register('formula_function', new JadawelHasOption(context))
    $registry.register('formula_function', new JadawelIsBlank(context))
    $registry.register('formula_function', new JadawelIsNull(context))
    $registry.register('formula_function', new JadawelNot(context))
    $registry.register('formula_function', new JadawelNotEqual(context))
    $registry.register('formula_function', new JadawelGreaterThan(context))
    $registry.register(
      'formula_function',
      new JadawelGreaterThanOrEqual(context)
    )
    $registry.register('formula_function', new JadawelLessThan(context))
    $registry.register('formula_function', new JadawelLessThanOrEqual(context))
    $registry.register('formula_function', new JadawelAnd(context))
    $registry.register('formula_function', new JadawelOr(context))
    // Date functions
    $registry.register('formula_function', new JadawelDatetimeFormat(context))
    $registry.register('formula_function', new JadawelDatetimeFormatTz(context))
    $registry.register('formula_function', new JadawelDay(context))
    $registry.register('formula_function', new JadawelNow(context))
    $registry.register('formula_function', new JadawelToday(context))
    $registry.register('formula_function', new JadawelToDateTz(context))
    $registry.register('formula_function', new JadawelToDate(context))
    $registry.register('formula_function', new JadawelDateDiff(context))
    // Date interval functions
    $registry.register('formula_function', new JadawelDateInterval(context))
    $registry.register(
      'formula_function',
      new JadawelDurationToSeconds(context)
    )
    $registry.register(
      'formula_function',
      new JadawelSecondsToDuration(context)
    )
    // Special functions. NOTE: rollup compatible functions are shown field sub-form in
    // the same order as they are listed here.
    $registry.register('formula_function', new JadawelAdd(context))
    $registry.register('formula_function', new JadawelMinus(context))
    $registry.register('formula_function', new JadawelField(context))
    $registry.register('formula_function', new JadawelLookup(context))
    $registry.register('formula_function', new JadawelRowId(context))
    $registry.register('formula_function', new JadawelContains(context))
    $registry.register('formula_function', new JadawelLeft(context))
    $registry.register('formula_function', new JadawelRight(context))
    $registry.register('formula_function', new JadawelTrim(context))
    $registry.register('formula_function', new JadawelRegexReplace(context))
    $registry.register('formula_function', new JadawelGreatest(context))
    $registry.register('formula_function', new JadawelLeast(context))
    $registry.register('formula_function', new JadawelMonth(context))
    $registry.register('formula_function', new JadawelYear(context))
    $registry.register('formula_function', new JadawelSecond(context))
    $registry.register('formula_function', new JadawelWhenEmpty(context))
    $registry.register('formula_function', new JadawelAny(context))
    $registry.register('formula_function', new JadawelEvery(context))
    $registry.register('formula_function', new JadawelMin(context))
    $registry.register('formula_function', new JadawelMax(context))
    $registry.register('formula_function', new JadawelCount(context))
    $registry.register('formula_function', new JadawelSum(context))
    $registry.register('formula_function', new JadawelAvg(context))
    $registry.register('formula_function', new JadawelJoin(context))
    $registry.register('formula_function', new JadawelStddevPop(context))
    $registry.register('formula_function', new JadawelStddevSample(context))
    $registry.register('formula_function', new JadawelVarianceSample(context))
    $registry.register('formula_function', new JadawelVariancePop(context))
    $registry.register('formula_function', new JadawelFilter(context))
    $registry.register('formula_function', new JadawelTrunc(context))
    $registry.register('formula_function', new JadawelIsNaN(context))
    $registry.register('formula_function', new JadawelWhenNaN(context))
    $registry.register('formula_function', new JadawelEven(context))
    $registry.register('formula_function', new JadawelOdd(context))
    $registry.register('formula_function', new JadawelAbs(context))
    $registry.register('formula_function', new JadawelCeil(context))
    $registry.register('formula_function', new JadawelFloor(context))
    $registry.register('formula_function', new JadawelSign(context))
    $registry.register('formula_function', new JadawelLog(context))
    $registry.register('formula_function', new JadawelExp(context))
    $registry.register('formula_function', new JadawelLn(context))
    $registry.register('formula_function', new JadawelPower(context))
    $registry.register('formula_function', new JadawelSqrt(context))
    $registry.register('formula_function', new JadawelRound(context))
    $registry.register('formula_function', new JadawelMod(context))
    // Link functions
    $registry.register('formula_function', new JadawelLink(context))
    $registry.register('formula_function', new JadawelButton(context))
    $registry.register('formula_function', new JadawelGetLinkUrl(context))
    $registry.register('formula_function', new JadawelGetLinkLabel(context))
    // File functions
    $registry.register(
      'formula_function',
      new JadawelGetFileVisibleName(context)
    )
    $registry.register('formula_function', new JadawelGetFileMimeType(context))
    $registry.register('formula_function', new JadawelGetFileSize(context))
    $registry.register('formula_function', new JadawelGetImageWidth(context))
    $registry.register('formula_function', new JadawelGetImageHeight(context))
    $registry.register('formula_function', new JadawelIsImage(context))

    $registry.register('formula_function', new JadawelGetFileCount(context))
    $registry.register('formula_function', new JadawelIndex(context))
    $registry.register('formula_function', new JadawelToUrl(context))
    $registry.register('formula_function', new JadawelArrayUnique(context))
    $registry.register('formula_function', new JadawelArraySlice(context))
    $registry.register('formula_function', new JadawelFirst(context))
    $registry.register('formula_function', new JadawelLast(context))

    // Formula Types
    $registry.register('formula_type', new JadawelFormulaTextType(context))
    $registry.register('formula_type', new JadawelFormulaCharType(context))
    $registry.register('formula_type', new JadawelFormulaBooleanType(context))
    $registry.register('formula_type', new JadawelFormulaDateType(context))
    $registry.register(
      'formula_type',
      new JadawelFormulaDateIntervalType(context)
    )
    $registry.register('formula_type', new JadawelFormulaDurationType(context))
    $registry.register('formula_type', new JadawelFormulaNumberType(context))
    $registry.register('formula_type', new JadawelFormulaArrayType(context))
    $registry.register('formula_type', new JadawelFormulaSpecialType(context))
    $registry.register('formula_type', new JadawelFormulaInvalidType(context))
    $registry.register(
      'formula_type',
      new JadawelFormulaSingleSelectType(context)
    )
    $registry.register('formula_type', new JadawelFormulaURLType(context))
    $registry.register(
      'formula_type',
      new JadawelFormulaMultipleSelectType(context)
    )
    $registry.register('formula_type', new JadawelFormulaButtonType(context))
    $registry.register('formula_type', new JadawelFormulaLinkType(context))
    $registry.register('formula_type', new JadawelFormulaFileType(context))
    $registry.register(
      'formula_type',
      new JadawelFormulaMultipleCollaboratorsType(context)
    )

    // File preview types
    $registry.register('preview', new ImageFilePreview(context))
    $registry.register('preview', new AudioFilePreview(context))
    $registry.register('preview', new VideoFilePreview(context))
    $registry.register('preview', new PDFBrowserFilePreview(context))
    $registry.register('preview', new GoogleDocFilePreview(context))

    $registry.register('viewAggregation', new MinViewAggregationType(context))
    $registry.register('viewAggregation', new MaxViewAggregationType(context))
    $registry.register('viewAggregation', new SumViewAggregationType(context))
    $registry.register(
      'viewAggregation',
      new AverageViewAggregationType(context)
    )
    $registry.register(
      'viewAggregation',
      new MedianViewAggregationType(context)
    )
    $registry.register(
      'viewAggregation',
      new StdDevViewAggregationType(context)
    )
    $registry.register(
      'viewAggregation',
      new VarianceViewAggregationType(context)
    )
    $registry.register(
      'viewAggregation',
      new EarliestDateViewAggregationType(context)
    )
    $registry.register(
      'viewAggregation',
      new LatestDateViewAggregationType(context)
    )
    $registry.register('viewAggregation', new CountViewAggregationType(context))
    $registry.register(
      'viewAggregation',
      new EmptyCountViewAggregationType(context)
    )
    $registry.register(
      'viewAggregation',
      new NotEmptyCountViewAggregationType(context)
    )
    $registry.register(
      'viewAggregation',
      new CheckedCountViewAggregationType(context)
    )
    $registry.register(
      'viewAggregation',
      new NotCheckedCountViewAggregationType(context)
    )
    $registry.register(
      'viewAggregation',
      new EmptyPercentageViewAggregationType(context)
    )
    $registry.register(
      'viewAggregation',
      new NotEmptyPercentageViewAggregationType(context)
    )
    $registry.register(
      'viewAggregation',
      new CheckedPercentageViewAggregationType(context)
    )
    $registry.register(
      'viewAggregation',
      new NotCheckedPercentageViewAggregationType(context)
    )
    $registry.register(
      'viewAggregation',
      new UniqueCountViewAggregationType(context)
    )
    $registry.register(
      'viewAggregation',
      new DistributionViewAggregationType(context)
    )

    $registry.register('formViewMode', new FormViewFormModeType(context))

    $registry.register(
      'databaseDataProvider',
      new FieldsDataProviderType(context)
    )

    // notifications
    $registry.register(
      'notification',
      new CollaboratorAddedToRowNotificationType(context)
    )
    $registry.register(
      'notification',
      new FormSubmittedNotificationType(context)
    )
    $registry.register(
      'notification',
      new UserMentionInRichTextFieldNotificationType(context)
    )
    $registry.register(
      'notification',
      new WebhookDeactivatedNotificationType(context)
    )
    $registry.register(
      'notification',
      new WebhookPayloadTooLargedNotificationType(context)
    )

    $registry.register(
      'rowModalSidebar',
      new HistoryRowModalSidebarType(context)
    )

    $registry.register('onboarding', new DatabaseOnboardingType(context))
    $registry.register(
      'onboarding',
      new DatabaseScratchTrackOnboardingType(context)
    )
    $registry.register(
      'onboarding',
      new DatabaseScratchTrackFieldsOnboardingType(context)
    )
    $registry.register('onboarding', new DatabaseImportOnboardingType(context))

    $registry.register(
      'databaseOnboardingStep',
      new ScratchDatabaseOnboardingStepType(context)
    )
    $registry.register(
      'databaseOnboardingStep',
      new ImportDatabaseOnboardingStepType(context)
    )
    $registry.register(
      'databaseOnboardingStep',
      new AirtableDatabaseOnboardingStepType(context)
    )
    $registry.register(
      'databaseOnboardingStep',
      new TemplateDatabaseOnboardingStepType(context)
    )

    $registry.register(
      'onboardingTrackFields',
      new DatabaseScratchTrackProjectFieldsOnboardingType(context)
    )
    $registry.register(
      'onboardingTrackFields',
      new DatabaseScratchTrackTeamFieldsOnboardingType(context)
    )
    $registry.register(
      'onboardingTrackFields',
      new DatabaseScratchTrackTaskFieldsOnboardingType(context)
    )
    $registry.register(
      'onboardingTrackFields',
      new DatabaseScratchTrackCampaignFieldsOnboardingType(context)
    )
    $registry.register(
      'onboardingTrackFields',
      new DatabaseScratchTrackCustomFieldsOnboardingType(context)
    )

    $registry.register(
      'configureDataSync',
      new SyncedFieldsConfigureDataSyncType(context)
    )
    $registry.register(
      'configureDataSync',
      new SettingsConfigureDataSyncType(context)
    )

    $registry.register('guidedTour', new DatabaseGuidedTourType(context))

    $registry.registerNamespace('fieldContextItem')

    searchTypeRegistry.register(new DatabaseSearchType(context))
    searchTypeRegistry.register(new DatabaseTableSearchType(context))
    searchTypeRegistry.register(new DatabaseFieldSearchType(context))
    searchTypeRegistry.register(new DatabaseRowSearchType(context))
  },
})
