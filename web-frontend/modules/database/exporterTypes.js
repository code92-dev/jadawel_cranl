import { Registerable } from '@jadawel/modules/core/registry'
import { GridViewType } from '@jadawel/modules/database/viewTypes'
import TableCSVExporter from '@jadawel/modules/database/components/export/TableCSVExporter'
import TableSpreadsheetExporter from '@jadawel/modules/database/components/export/TableSpreadsheetExporter'

export class TableExporterType extends Registerable {
  /**
   * Should return a icon class name class name related to the icon that must be displayed
   * to the user.
   */
  getIconClass() {
    throw new Error('The icon class of an exporter type must be set.')
  }

  /**
   * Should return a human readable name that indicating what the exporter does.
   */
  getName() {
    throw new Error('The name of an exporter type must be set.')
  }

  /**
   * Should return the component that is added to the ExportTableModal when the
   * exporter is chosen. It should handle all the user input and additional form
   * fields and it should generate a compatible data object that must be added to
   * the form values.
   */
  getFormComponent() {
    return null
  }

  /**
   * Whether this exporter type supports exporting just the table without a view.
   */
  getCanExportTable() {
    throw new Error(
      'Whether an exporter type can export just tables must be set.'
    )
  }

  getFileExtension() {
    return this.getType()
  }

  /**
   * The supported view types for this exporter.
   */
  getSupportedViews() {
    throw new Error(
      'The supported view types for an exporter type must be set.'
    )
  }

  constructor(...args) {
    super(...args)
    this.type = this.getType()
    this.iconClass = this.getIconClass()
    this.canExportTable = this.getCanExportTable()
    this.supportedViews = this.getSupportedViews()

    if (this.type === null) {
      throw new Error('The type name of an exporter type must be set.')
    }
  }

  serialize() {
    return {
      type: this.type,
      iconClass: this.iconClass,
      canExportTable: this.canExportTable,
      supportedViews: this.supportedViews,
    }
  }

  /**
   * If the exporter type is disabled, this text will be visible explaining why.
   */
  getDeactivatedText() {}

  /**
   * When the disabled exporter is clicked, this modal will be shown.
   */
  getDeactivatedClickModal() {
    return null
  }

  /**
   * Indicates if the exporter type is disabled.
   */
  isDeactivated(workspaceId) {
    return false
  }
}

export class CSVTableExporterType extends TableExporterType {
  static getType() {
    return 'csv'
  }

  getIconClass() {
    return 'jadawel-icon-file-csv'
  }

  getName() {
    const { $i18n: i18n } = this.app
    return i18n.t('exporterType.csv')
  }

  getFormComponent() {
    return TableCSVExporter
  }

  getCanExportTable() {
    return true
  }

  getSupportedViews() {
    return [GridViewType.getType()]
  }
}

export class XlsxTableExporterType extends TableExporterType {
  static getType() {
    return 'xlsx'
  }

  getIconClass() {
    return 'jadawel-icon-file-excel'
  }

  getName() {
    const { $i18n: i18n } = this.app
    return i18n.t('exporterType.xlsx')
  }

  getFormComponent() {
    return TableSpreadsheetExporter
  }

  getCanExportTable() {
    return true
  }

  getSupportedViews() {
    return [GridViewType.getType()]
  }
}

export class OdsTableExporterType extends TableExporterType {
  static getType() {
    return 'ods'
  }

  getIconClass() {
    return 'jadawel-icon-file-excel'
  }

  getName() {
    const { $i18n: i18n } = this.app
    return i18n.t('exporterType.ods')
  }

  getFormComponent() {
    return TableSpreadsheetExporter
  }

  getCanExportTable() {
    return true
  }

  getSupportedViews() {
    return [GridViewType.getType()]
  }
}
