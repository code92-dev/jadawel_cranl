import { defineAsyncComponent } from 'vue'
import {
  SummaryWidgetType,
  WidgetType,
} from '@jadawel/modules/dashboard/widgetTypes'
import { DEFAULT_MIN_SIZE } from '@jadawel/modules/arabase/dashboard/layout'
import KpiSvg from '@jadawel/modules/arabase/assets/images/widgets/kpi_widget.svg?url'
import ProgressSvg from '@jadawel/modules/arabase/assets/images/widgets/progress_widget.svg?url'
import GaugeSvg from '@jadawel/modules/arabase/assets/images/widgets/gauge_widget.svg?url'
import BarChartSvg from '@jadawel/modules/arabase/assets/images/widgets/bar_chart_widget.svg?url'
import HorizontalBarChartSvg from '@jadawel/modules/arabase/assets/images/widgets/horizontal_bar_chart_widget.svg?url'
import LineChartSvg from '@jadawel/modules/arabase/assets/images/widgets/line_chart_widget.svg?url'
import AreaChartSvg from '@jadawel/modules/arabase/assets/images/widgets/area_chart_widget.svg?url'
import PieChartSvg from '@jadawel/modules/arabase/assets/images/widgets/pie_chart_widget.svg?url'
import DoughnutChartSvg from '@jadawel/modules/arabase/assets/images/widgets/doughnut_chart_widget.svg?url'
import RecordsListSvg from '@jadawel/modules/arabase/assets/images/widgets/records_list_widget.svg?url'
import UpcomingDatesSvg from '@jadawel/modules/arabase/assets/images/widgets/upcoming_dates_widget.svg?url'
import TextSectionSvg from '@jadawel/modules/arabase/assets/images/widgets/text_section_widget.svg?url'
import TextNoteSvg from '@jadawel/modules/arabase/assets/images/widgets/text_note_widget.svg?url'
import TextCalloutSvg from '@jadawel/modules/arabase/assets/images/widgets/text_callout_widget.svg?url'

const lazy = (name) =>
  defineAsyncComponent(
    () =>
      import(`@jadawel/modules/arabase/dashboard/components/widget/${name}.vue`)
  )

const KpiWidget = lazy('KpiWidget')
const KpiWidgetSettings = lazy('KpiWidgetSettings')
const ChartWidget = lazy('ChartWidget')
const ChartWidgetSettings = lazy('ChartWidgetSettings')
const ProgressWidget = lazy('ProgressWidget')
const ProgressWidgetSettings = lazy('ProgressWidgetSettings')
const RecordsListWidget = lazy('RecordsListWidget')
const RecordsListWidgetSettings = lazy('RecordsListWidgetSettings')
const UpcomingDatesWidget = lazy('UpcomingDatesWidget')
const UpcomingDatesWidgetSettings = lazy('UpcomingDatesWidgetSettings')
const TextWidget = lazy('TextWidget')
const TextWidgetSettings = lazy('TextWidgetSettings')

/**
 * The widget gallery's sections, in the order they are shown.
 */
export const WIDGET_CATEGORIES = ['numbers', 'charts', 'lists', 'text']

/**
 * The chart types, shared by the gallery tiles and the settings picker.
 */
export const CHART_TYPES = [
  {
    value: 'bar',
    nameKey: 'chartWidget.bar',
    descriptionKey: 'widgetGallery.description.bar',
    icon: 'iconoir-stats-report',
    image: BarChartSvg,
    size: { width: 6, height: 4 },
  },
  {
    value: 'horizontal_bar',
    nameKey: 'chartWidget.horizontalBar',
    descriptionKey: 'widgetGallery.description.horizontalBar',
    icon: 'iconoir-align-left',
    image: HorizontalBarChartSvg,
    size: { width: 6, height: 4 },
  },
  {
    value: 'line',
    nameKey: 'chartWidget.line',
    descriptionKey: 'widgetGallery.description.line',
    icon: 'iconoir-graph-up',
    image: LineChartSvg,
    size: { width: 8, height: 4 },
  },
  {
    value: 'area',
    nameKey: 'chartWidget.area',
    descriptionKey: 'widgetGallery.description.area',
    icon: 'iconoir-stats-up-square',
    image: AreaChartSvg,
    size: { width: 8, height: 4 },
  },
  {
    value: 'doughnut',
    nameKey: 'chartWidget.doughnut',
    descriptionKey: 'widgetGallery.description.doughnut',
    icon: 'iconoir-percentage-circle',
    image: DoughnutChartSvg,
    size: { width: 4, height: 4 },
  },
  {
    value: 'pie',
    nameKey: 'chartWidget.pie',
    descriptionKey: 'widgetGallery.description.pie',
    icon: 'iconoir-half-cookie',
    image: PieChartSvg,
    size: { width: 4, height: 4 },
  },
]

/**
 * Gallery metadata every fork widget type provides: which section it is listed
 * in, the size it is created at and the smallest it can be resized to. A
 * variation may carry its own `size` and `description`.
 */
const withGallery = (Base) =>
  class extends Base {
    get category() {
      return 'numbers'
    }

    get defaultSize() {
      return { width: 4, height: 4 }
    }

    get minSize() {
      return DEFAULT_MIN_SIZE
    }

    get description() {
      return ''
    }

    /**
     * Whether the widget draws its own card. A section heading sits on the
     * canvas without one.
     */
    isBare(widget) {
      return false
    }

    get variations() {
      return super.variations.map((variation) => ({
        category: this.category,
        description: this.description,
        size: this.defaultSize,
        ...variation,
      }))
    }
  }

/**
 * A widget whose data arrives as one dispatch of its data source.
 *
 * Such a widget is loading until that dispatch lands. The base class returns
 * `false` unconditionally, which would show an empty widget instead of a
 * skeleton on first paint.
 */
export class DataSourceWidgetType extends withGallery(WidgetType) {
  isLoading(widget, data) {
    const dataSourceId = widget.data_source_id
    return !(data[dataSourceId] && Object.keys(data[dataSourceId]).length !== 0)
  }
}

/**
 * Upstream's `summary` widget, drawn by the fork as a key-number card with an
 * icon, an accent and a formatted number. Same type name and API, so existing
 * dashboards and templates pick the new look up as they are.
 */
export class KpiWidgetType extends withGallery(SummaryWidgetType) {
  get name() {
    return this.app.$i18n.t('kpiWidget.name')
  }

  get description() {
    return this.app.$i18n.t('widgetGallery.description.kpi')
  }

  get createWidgetImage() {
    return KpiSvg
  }

  get component() {
    return KpiWidget
  }

  get settingsComponent() {
    return KpiWidgetSettings
  }

  get defaultSize() {
    return { width: 3, height: 2 }
  }

  get minSize() {
    return { width: 2, height: 2 }
  }

  getOrder() {
    return 0
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

  get minSize() {
    return { width: 2, height: 2 }
  }

  get variations() {
    const { $i18n: i18n } = this.app
    return [
      {
        name: i18n.t('progressWidget.name'),
        description: i18n.t('widgetGallery.description.progress'),
        createWidgetImage: ProgressSvg,
        type: this,
        params: { display_style: 'bar' },
        size: { width: 3, height: 2 },
        category: 'numbers',
        dropdownIcon: 'iconoir-percentage',
      },
      {
        name: i18n.t('progressWidget.gaugeName'),
        description: i18n.t('widgetGallery.description.gauge'),
        createWidgetImage: GaugeSvg,
        type: this,
        params: { display_style: 'gauge' },
        size: { width: 3, height: 3 },
        category: 'numbers',
        dropdownIcon: 'iconoir-dashboard-speed',
      },
    ]
  }

  getOrder() {
    return 5
  }
}

/**
 * One widget type presented as six tiles.
 *
 * The chart types need identical configuration and users routinely try one
 * then switch, so they are variations of a single `chart` type rather than six
 * types. A variation only decides which `chart_type` the widget is created
 * with; the settings panel can change it afterwards.
 */
export class ChartWidgetType extends DataSourceWidgetType {
  static getType() {
    return 'chart'
  }

  get name() {
    return this.app.$i18n.t('chartWidget.name')
  }

  get category() {
    return 'charts'
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

  get minSize() {
    return { width: 3, height: 3 }
  }

  get variations() {
    const { $i18n: i18n } = this.app
    return CHART_TYPES.map((chartType) => ({
      name: i18n.t(chartType.nameKey),
      description: i18n.t(chartType.descriptionKey),
      createWidgetImage: chartType.image,
      type: this,
      params: { chart_type: chartType.value },
      size: chartType.size,
      category: 'charts',
      dropdownIcon: chartType.icon,
    }))
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

  get description() {
    return this.app.$i18n.t('widgetGallery.description.recordsList')
  }

  get category() {
    return 'lists'
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

  get defaultSize() {
    return { width: 8, height: 5 }
  }

  get minSize() {
    return { width: 4, height: 3 }
  }

  getOrder() {
    return 20
  }
}

export class UpcomingDatesWidgetType extends DataSourceWidgetType {
  static getType() {
    return 'upcoming_dates'
  }

  get name() {
    return this.app.$i18n.t('upcomingDatesWidget.name')
  }

  get description() {
    return this.app.$i18n.t('widgetGallery.description.upcomingDates')
  }

  get category() {
    return 'lists'
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

  get defaultSize() {
    return { width: 4, height: 5 }
  }

  get minSize() {
    return { width: 3, height: 3 }
  }

  getOrder() {
    return 40
  }
}

/**
 * Words on the board — a section heading, a note or a callout. It owns no data
 * source, so it is never loading.
 */
export class TextWidgetType extends withGallery(WidgetType) {
  static getType() {
    return 'text'
  }

  get name() {
    return this.app.$i18n.t('textWidget.name')
  }

  get category() {
    return 'text'
  }

  get createWidgetImage() {
    return TextNoteSvg
  }

  get component() {
    return TextWidget
  }

  get settingsComponent() {
    return TextWidgetSettings
  }

  get minSize() {
    return { width: 2, height: 1 }
  }

  isBare(widget) {
    return widget.text_style === 'section'
  }

  get variations() {
    const { $i18n: i18n } = this.app
    const variation = (style, image, size, icon) => ({
      name: i18n.t(`textWidget.${style}`),
      description: i18n.t(`widgetGallery.description.${style}`),
      createWidgetImage: image,
      type: this,
      params: { text_style: style },
      size,
      category: 'text',
      dropdownIcon: icon,
    })
    return [
      variation(
        'section',
        TextSectionSvg,
        { width: 12, height: 1 },
        'iconoir-text'
      ),
      variation('note', TextNoteSvg, { width: 4, height: 2 }, 'iconoir-page'),
      variation(
        'callout',
        TextCalloutSvg,
        { width: 6, height: 2 },
        'iconoir-light-bulb'
      ),
    ]
  }

  getOrder() {
    return 50
  }
}
