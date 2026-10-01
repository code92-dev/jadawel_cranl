import Alert from '@jadawel/modules/core/components/Alert'
import Avatar from '@jadawel/modules/core/components/Avatar'
import Badge from '@jadawel/modules/core/components/Badge'
import BadgeCollaborator from '@jadawel/modules/core/components/BadgeCollaborator'
import Button from '@jadawel/modules/core/components/Button'
import ButtonAdd from '@jadawel/modules/core/components/ButtonAdd'
import ButtonFloating from '@jadawel/modules/core/components/ButtonFloating'
import ButtonIcon from '@jadawel/modules/core/components/ButtonIcon'
import ButtonText from '@jadawel/modules/core/components/ButtonText'
import CallToAction from '@jadawel/modules/core/components/CallToAction.vue'
import Checkbox from '@jadawel/modules/core/components/Checkbox'
import Chips from '@jadawel/modules/core/components/Chips'
import ColorInput from '@jadawel/modules/core/components/ColorInput'
import Context from '@jadawel/modules/core/components/Context'
import Copied from '@jadawel/modules/core/components/Copied'
import DownloadLink from '@jadawel/modules/core/components/DownloadLink'
import Dropdown from '@jadawel/modules/core/components/Dropdown'
import DropdownItem from '@jadawel/modules/core/components/DropdownItem'
import DropdownSection from '@jadawel/modules/core/components/DropdownSection'
import Editable from '@jadawel/modules/core/components/Editable'
import Error from '@jadawel/modules/core/components/Error'
import Expandable from '@jadawel/modules/core/components/Expandable.vue'
import FormElement from '@jadawel/modules/core/components/FormElement'
import FormGroup from '@jadawel/modules/core/components/FormGroup'
import FormInput from '@jadawel/modules/core/components/FormInput'
import FormRow from '@jadawel/modules/core/components/FormRow'
import FormSection from '@jadawel/modules/core/components/FormSection'
import FormTextarea from '@jadawel/modules/core/components/FormTextarea'
import HelpIcon from '@jadawel/modules/core/components/HelpIcon'
import Icon from '@jadawel/modules/core/components/Icon'
import ImageInput from '@jadawel/modules/core/components/ImageInput'
import List from '@jadawel/modules/core/components/List'
import Logo from '@jadawel/modules/core/components/Logo'
import MarkdownIt from '@jadawel/modules/core/components/MarkdownIt'
import Modal from '@jadawel/modules/core/components/Modal'
import Picker from '@jadawel/modules/core/components/Picker'
import Presentation from '@jadawel/modules/core/components/Presentation'
import ProgressBar from '@jadawel/modules/core/components/ProgressBar'
import Radio from '@jadawel/modules/core/components/Radio'
import RadioButton from '@jadawel/modules/core/components/RadioButton'
import RadioCard from '@jadawel/modules/core/components/RadioCard'
import RadioGroup from '@jadawel/modules/core/components/RadioGroup'
import ReadOnlyForm from '@jadawel/modules/core/components/ReadOnlyForm'
import Scrollbars from '@jadawel/modules/core/components/Scrollbars'
import SegmentControl from '@jadawel/modules/core/components/SegmentControl'
import SelectSearch from '@jadawel/modules/core/components/SelectSearch'
import SwitchButton from '@jadawel/modules/core/components/SwitchButton'
import SwitchInput from '@jadawel/modules/core/components/SwitchInput'
import Tab from '@jadawel/modules/core/components/Tab'
import Tabs from '@jadawel/modules/core/components/Tabs'
import Thumbnail from '@jadawel/modules/core/components/Thumbnail'
import SkeletonBlock from '@jadawel/modules/core/components/SkeletonBlock'
import autoOverflowScroll from '@jadawel/modules/core/directives/autoOverflowScroll'
import autoScroll from '@jadawel/modules/core/directives/autoScroll'
import clickOutside from '@jadawel/modules/core/directives/clickOutside'
import preventParentScroll from '@jadawel/modules/core/directives/preventParentScroll'
import scroll from '@jadawel/modules/core/directives/scroll'
import sortable from '@jadawel/modules/core/directives/sortable'
import tooltip from '@jadawel/modules/core/directives/tooltip'
import userFileUpload from '@jadawel/modules/core/directives/userFileUpload'

function setupVue(app) {
  app.component('Context', Context)
  app.component('Modal', Modal)
  app.component('Editable', Editable)
  app.component('Dropdown', Dropdown)
  app.component('DropdownSection', DropdownSection)
  app.component('DropdownItem', DropdownItem)
  app.component('Checkbox', Checkbox)
  app.component('Radio', Radio)
  app.component('RadioGroup', RadioGroup)
  app.component('RadioCard', RadioCard)
  app.component('Scrollbars', Scrollbars)
  app.component('Alert', Alert)
  app.component('Error', Error)
  app.component('SwitchInput', SwitchInput)
  app.component('Copied', Copied)
  app.component('MarkdownIt', MarkdownIt)
  app.component('DownloadLink', DownloadLink)
  app.component('FormElement', FormElement)
  app.component('Picker', Picker)
  app.component('ProgressBar', ProgressBar)
  app.component('Tab', Tab)
  app.component('Tabs', Tabs)
  app.component('List', List)
  app.component('HelpIcon', HelpIcon)
  app.component('Badge', Badge)
  app.component('BadgeCollaborator', BadgeCollaborator)
  app.component('Expandable', Expandable)
  app.component('Button', Button)
  app.component('ButtonText', ButtonText)
  app.component('ButtonFloating', ButtonFloating)
  app.component('ButtonAdd', ButtonAdd)
  app.component('ButtonIcon', ButtonIcon)
  app.component('Chips', Chips)
  app.component('RadioButton', RadioButton)
  app.component('Thumbnail', Thumbnail)
  app.component('Avatar', Avatar)
  app.component('Presentation', Presentation)
  app.component('FormInput', FormInput)
  app.component('FormTextarea', FormTextarea)
  app.component('CallToAction', CallToAction)
  app.component('FormGroup', FormGroup)
  app.component('FormRow', FormRow)
  app.component('ColorInput', ColorInput)
  app.component('ImageInput', ImageInput)
  app.component('SelectSearch', SelectSearch)
  app.component('Logo', Logo)
  app.component('ReadOnlyForm', ReadOnlyForm)
  app.component('FormSection', FormSection)
  app.component('SegmentControl', SegmentControl)
  app.component('SwitchButton', SwitchButton)
  app.component('Icon', Icon)
  app.component('SkeletonBlock', SkeletonBlock)

  app.directive('scroll', scroll)
  app.directive('preventParentScroll', preventParentScroll)
  app.directive('tooltip', tooltip)
  app.directive('sortable', sortable)
  app.directive('autoOverflowScroll', autoOverflowScroll)
  app.directive('userFileUpload', userFileUpload)
  app.directive('autoScroll', autoScroll)
  app.directive('clickOutside', clickOutside)

  app.config.globalProperties.$super = function (options) {
    return new Proxy(options, {
      get: (opts, name) => {
        if (opts.methods && name in opts.methods) {
          return opts.methods[name].bind(this)
        }
      },
    })
  }
}

export default defineNuxtPlugin((nuxtApp) => {
  setupVue(nuxtApp.vueApp)
})

export { setupVue }
