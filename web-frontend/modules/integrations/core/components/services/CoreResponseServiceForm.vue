<template>
  <form @submit.prevent>
    <FormGroup
      class="margin-bottom-2"
      small-label
      required
      :label="$t('coreResponseServiceForm.statusCode')"
    >
      <!--
        Jadawel fork: upstream renders this through the formula input's raw
        mode, which the fork's formula input does not have. The form switches
        between a status code picker (a raw formula) and a formula itself.
      -->
      <Dropdown
        v-if="statusCodeIsRaw"
        :model-value="values.status_code.formula"
        @update:model-value="setRawStatusCode"
      >
        <DropdownItem
          v-for="statusCode in statusCodes"
          :key="statusCode.value"
          :name="statusCode.name"
          :value="statusCode.value"
        />
      </Dropdown>
      <InjectedFormulaInput v-else v-model="values.status_code" />
      <ButtonText
        class="margin-top-1"
        type="secondary"
        size="small"
        :icon="statusCodeIsRaw ? 'iconoir-sigma-function' : 'iconoir-list'"
        @click="toggleStatusCodeMode"
      >
        {{
          statusCodeIsRaw
            ? $t('coreResponseServiceForm.statusCodeUseFormula')
            : $t('coreResponseServiceForm.statusCodeUseList')
        }}
      </ButtonText>
    </FormGroup>

    <FormGroup
      v-if="canHaveBody"
      class="margin-bottom-2"
      small-label
      required
      :label="$t('coreResponseServiceForm.bodyType')"
    >
      <Dropdown v-model="bodyType">
        <DropdownItem
          v-for="responseBodyType in bodyTypes"
          :key="responseBodyType.value"
          :name="responseBodyType.name"
          :value="responseBodyType.value"
        />
      </Dropdown>
    </FormGroup>

    <FormGroup
      v-if="canHaveBody && values.body_type !== 'empty'"
      class="margin-bottom-2"
      small-label
      :label="$t('coreResponseServiceForm.body')"
    >
      <InjectedFormulaInput
        v-model="values.body"
        :placeholder="$t('coreResponseServiceForm.bodyPlaceholder')"
        textarea
      />
    </FormGroup>

    <FormGroup
      class="margin-bottom-2"
      small-label
      :label="$t('coreResponseServiceForm.headers')"
    >
      <template v-if="v$.values.headers.$model.length">
        <div class="row service-form__row">
          <label class="col col-5 control__label control__label--small">
            {{ $t('coreResponseServiceForm.name') }}
          </label>
          <label class="col col-7 control__label control__label--small">
            {{ $t('coreResponseServiceForm.value') }}
          </label>
        </div>
        <div
          v-for="(header, index) in v$.values.headers.$model"
          :key="header.id"
          class="row service-form__row margin-bottom-1"
        >
          <div class="col col-5">
            <FormInput
              v-model="header.key"
              :error="!!v$.values.headers.$each.$message[index]?.[0]"
              :placeholder="$t('coreResponseServiceForm.namePlaceholder')"
              @blur="v$.values.headers.$touch()"
            />
          </div>
          <div class="col col-5">
            <InjectedFormulaInput
              v-model="header.value"
              :placeholder="$t('coreResponseServiceForm.valuePlaceholder')"
            />
          </div>
          <div class="col col-2">
            <ButtonIcon icon="iconoir-bin" @click="deleteHeader(header)" />
          </div>
          <div
            v-show="v$.values.headers.$each.$message[index]?.[0]"
            class="error margin-left-1"
          >
            {{ v$.values.headers.$each.$message[index]?.[0] }}
          </div>
        </div>
      </template>
      <ButtonText
        type="secondary"
        size="small"
        icon="iconoir-plus"
        @click="createHeader"
      >
        {{ $t('coreResponseServiceForm.addHeader') }}
      </ButtonText>
    </FormGroup>
  </form>
</template>

<script>
import form from '@jadawel/modules/core/mixins/form'
import InjectedFormulaInput from '@jadawel/modules/core/components/formula/InjectedFormulaInput'
import { uuid } from '@jadawel/modules/core/utils/string'
import { useVuelidate } from '@vuelidate/core'
import { helpers, maxLength, required } from '@vuelidate/validators'

export default {
  name: 'CoreResponseServiceForm',
  components: { InjectedFormulaInput },
  mixins: [form],
  setup() {
    return { v$: useVuelidate() }
  },
  data() {
    return {
      allowedValues: ['status_code', 'body_type', 'body', 'headers'],
      values: {
        status_code: { formula: '204', mode: 'raw' },
        body_type: 'empty',
        body: {},
        headers: [],
      },
    }
  },
  computed: {
    bodyType: {
      get() {
        return this.values.body_type
      },
      set(bodyType) {
        if (bodyType === 'empty') {
          this.values.body = {
            formula: '',
            mode: 'simple',
            version: '0.1',
          }
        } else if (bodyType === 'json' && !this.values.body?.formula?.trim()) {
          this.values.body = {
            formula: "'{}'",
            mode: 'simple',
            version: '0.1',
          }
        }
        this.values.body_type = bodyType
      },
    },
    statusCodeIsRaw() {
      return this.values.status_code?.mode === 'raw'
    },
    canHaveBody() {
      const statusCode = this.values.status_code
      return statusCode?.mode !== 'raw' || statusCode.formula !== '204'
    },
    statusCodes() {
      return [200, 201, 202, 204, 400, 401, 403, 404, 405, 409, 422, 429].map(
        (value) => ({
          value: value.toString(),
          name: this.$t(`coreResponseServiceForm.statusCode${value}`),
        })
      )
    },
    bodyTypes() {
      return [
        {
          name: this.$t('coreResponseServiceForm.bodyTypeEmpty'),
          value: 'empty',
        },
        {
          name: this.$t('coreResponseServiceForm.bodyTypeJson'),
          value: 'json',
        },
        {
          name: this.$t('coreResponseServiceForm.bodyTypeText'),
          value: 'text',
        },
      ]
    },
  },
  methods: {
    setRawStatusCode(value) {
      this.values.status_code = { formula: value, mode: 'raw' }
    },
    toggleStatusCodeMode() {
      if (this.statusCodeIsRaw) {
        // A simple formula holds literal text as a quoted string.
        this.values.status_code = {
          formula: `'${this.values.status_code.formula}'`,
          mode: 'simple',
          version: '0.1',
        }
      } else {
        this.values.status_code = { formula: '204', mode: 'raw' }
      }
    },
    createHeader() {
      this.v$.values.headers.$model.push({
        key: `header${this.v$.values.headers.$model.length + 1}`,
        value: { formula: '', mode: 'simple' },
        id: uuid(),
      })
    },
    deleteHeader({ id }) {
      this.v$.values.headers.$model = this.v$.values.headers.$model.filter(
        (header) => header.id !== id
      )
    },
  },
  validations() {
    const isValidHeaderName = (name) => {
      const validNameRegex = /^[a-zA-Z0-9-_]+$/
      if (!name || name[0] === '-' || name[0] === '_') {
        return false
      }
      return validNameRegex.test(name)
    }

    return {
      values: {
        status_code: {},
        headers: {
          $each: helpers.forEach({
            key: {
              required: helpers.withMessage(
                this.$t('coreResponseServiceForm.nameFieldRequired'),
                required
              ),
              maxLength: helpers.withMessage(
                this.$t('error.maxLength', { max: 255 }),
                maxLength(255)
              ),
              invalid: helpers.withMessage(
                this.$t('coreResponseServiceForm.nameFieldInvalid'),
                isValidHeaderName
              ),
            },
            value: {},
          }),
        },
      },
    }
  },
}
</script>
