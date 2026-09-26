import { defineAsyncComponent } from 'vue'
import { WidgetType } from '@jadawel/modules/dashboard/widgetTypes'
import BarChartSvg from '@jadawel/modules/arabase/assets/images/widgets/bar_chart_widget.svg?url'
import LineChartSvg from '@jadawel/modules/arabase/assets/images/widgets/line_chart_widget.svg?url'
import PieChartSvg from '@jadawel/modules/arabase/assets/images/widgets/pie_chart_widget.svg?url'
import DoughnutChartSvg from '@jadawel/modules/arabase/assets/images/widgets/doughnut_chart_widget.svg?url'
import RecordsListSvg from '@jadawel/modules/arabase/assets/images/widgets/records_list_widget.svg?url'
import ProgressSvg from '@jadawel/modules/arabase/assets/images/widgets/progress_widget.svg?url'
import UpcomingDatesSvg from '@jadawel/modules/arabase/assets/images/widgets/upcoming_dates_widget.svg?url'

const ChartWidget = defineAsyncComponent(
  () =>
    import('@jadawel/modules/arabase/dashboard/components/widget/ChartWidget')
)
const ChartWidgetSettings = defineAsyncComponent(
  () =>
    import('@jadawel/modules/arabase/dashboard/components/widget/ChartWidgetSettings')
)
const ProgressWidget = defineAsyncComponent(
  () =>
    import('@jadawel/modules/arabase/dashboard/components/widget/ProgressWidget')
)
const ProgressWidgetSettings = defineAsyncComponent(
  () =>
    import('@jadawel/modules/arabase/dashboard/components/widget/ProgressWidgetSettings')
)
const RecordsListWidget = defineAsyncComponent(
  () =>
    import('@jadawel/modules/arabase/dashboard/components/widget/RecordsListWidget')
)
const RecordsListWidgetSettings = defineAsyncComponent(
  () =>
    import('@jadawel/modules/arabase/dashboard/components/widget/RecordsListWidgetSettings')
)
const UpcomingDatesWidget = defineAsyncComponent(
  () =>
    import('@jadawel/modules/arabase/dashboard/components/widget/UpcomingDatesWidget')
)
const UpcomingDatesWidgetSettings = defineAsyncComponent(
  () =>
    import('@jadawel/modules/arabase/dashboard/components/widget/UpcomingDatesWidgetSettings')
)

/**
 * A widget whose data arrives as one dispatch of its data source.
 *
 * Such a widget is loading until that dispatch lands. The base class returns
 * `false` unconditionally, which would show an empty widget instead of a
 * spinner on first paint.
 */
export class DataSourceWidgetType extends WidgetType {
  isLoading(widget, data) {
    const dataSourceId = widget.data_source_id
    return !(data[dataSourceId] && Object.keys(data[dataSourceId]).length !== 0)
  }
}

/**
 * One widget type presented as four tiles.
 *
 * Bar, line, pie and doughnut need identical configuration and users routinely
 * try one then switch, so they are variations of a single `chart` type rather
 * than four types. A variation only decides which `chart_type` the widget is
 * created with; the settings panel can change it afterwards.
 */
export class ChartWidgetType extends DataSourceWidgetType {
  static getType() {
    return 'chart'
  }

  get name() {
    return this.app.$i18n.t('chartWidget.name')
  }

  get createWidgetImage() {
    return BarChartSvg
  }

  get component() {
    return ChartWidget
  }

  get settingsComponent() {
    return ChartWidgetSettings
  }

  get variations() {
    const { $i18n: i18n } = this.app
    return [
      {
        name: i18n.t('chartWidget.bar'),
        createWidgetImage: BarChartSvg,
        type: this,
        params: { chart_type: 'bar' },
        dropdownIcon: 'iconoir-bar-chart',
      },
      {
        name: i18n.t('chartWidget.line'),
        createWidgetImage: LineChartSvg,
        type: this,
        params: { chart_type: 'line' },
        dropdownIcon: 'iconoir-graph-up',
      },
      {
        name: i18n.t('chartWidget.pie'),
        createWidgetImage: PieChartSvg,
        type: this,
        params: { chart_type: 'pie' },
        dropdownIcon: 'iconoir-pie-chart',
      },
      {
        name: i18n.t('chartWidget.doughnut'),
        createWidgetImage: DoughnutChartSvg,
        type: this,
        params: { chart_type: 'doughnut' },
        dropdownIcon: 'iconoir-pie-chart',
      },
    ]
  }

  getOrder() {
    return 10
  }
}

export class RecordsListWidgetType extends DataSourceWidgetType {
  static getType() {
    return 'records_list'
  }

  get name() {
    return this.app.$i18n.t('recordsListWidget.name')
  }

  get createWidgetImage() {
    return RecordsListSvg
  }

  get component() {
    return RecordsListWidget
  }

  get settingsComponent() {
    return RecordsListWidgetSettings
  }

  getOrder() {
    return 20
  }
}

export class ProgressWidgetType extends DataSourceWidgetType {
  static getType() {
    return 'progress'
  }

  get name() {
    return this.app.$i18n.t('progressWidget.name')
  }

  get createWidgetImage() {
    return ProgressSvg
  }

  get component() {
    return ProgressWidget
  }

  get settingsComponent() {
    return ProgressWidgetSettings
  }

  getOrder() {
    return 30
  }
}

export class UpcomingDatesWidgetType extends DataSourceWidgetType {
  static getType() {
    return 'upcoming_dates'
  }

  get name() {
    return this.app.$i18n.t('upcomingDatesWidget.name')
  }

  get createWidgetImage() {
    return UpcomingDatesSvg
  }

  get component() {
    return UpcomingDatesWidget
  }

  get settingsComponent() {
    return UpcomingDatesWidgetSettings
  }

  getOrder() {
    return 40
  }
}
