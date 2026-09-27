<template>
  <div id="generative-ai" class="admin-settings__group admin-ai">
    <h2 class="admin-settings__group-title">{{ $t('adminAI.title') }}</h2>
    <p class="admin-ai__intro">{{ $t('adminAI.description') }}</p>

    <div v-if="loading" class="loading"></div>

    <div
      v-for="provider in providers"
      v-else
      :key="provider.type"
      class="admin-settings__item admin-ai__provider"
    >
      <div class="admin-settings__label">
        <div class="admin-settings__name admin-ai__name">
          {{ providerName(provider.type) }}
          <Badge
            :color="provider.enabled ? 'green' : 'neutral'"
            size="small"
            rounded
            >{{
              provider.enabled ? $t('adminAI.active') : $t('adminAI.inactive')
            }}</Badge
          >
        </div>
        <div class="admin-settings__description">
          {{ $t(`adminAI.providers.${provider.type}`) }}
        </div>
        <div
          v-if="provider.configured_by_environment"
          class="admin-settings__description admin-ai__env"
        >
          {{ $t('adminAI.environmentNote') }}
        </div>
      </div>

      <form
        class="admin-settings__control admin-ai__form"
        @submit.prevent="save(provider)"
      >
        <label v-if="has(provider, 'api_key')" class="admin-ai__field">
          <span class="admin-ai__field-label">{{ $t('adminAI.apiKey') }}</span>
          <FormInput
            v-model="drafts[provider.type].api_key"
            type="password"
            dir="ltr"
            autocomplete="off"
            :placeholder="
              provider.api_key_set
                ? $t('adminAI.apiKeySaved', { hint: provider.api_key_hint })
                : $t('adminAI.apiKeyPlaceholder')
            "
          />
          <a
            v-if="provider.api_key_set"
            class="admin-ai__clear"
            @click.prevent="clearKey(provider)"
            >{{ $t('adminAI.removeKey') }}</a
          >
        </label>

        <label v-if="has(provider, 'host')" class="admin-ai__field">
          <span class="admin-ai__field-label">{{ $t('adminAI.host') }}</span>
          <FormInput
            v-model="drafts[provider.type].host"
            dir="ltr"
            placeholder="http://localhost:11434"
          />
        </label>

        <label v-if="has(provider, 'base_url')" class="admin-ai__field">
          <span class="admin-ai__field-label">{{ $t('adminAI.baseUrl') }}</span>
          <FormInput
            v-model="drafts[provider.type].base_url"
            dir="ltr"
            placeholder="https://api.openai.com/v1"
          />
        </label>

        <label v-if="has(provider, 'organization')" class="admin-ai__field">
          <span class="admin-ai__field-label">{{
            $t('adminAI.organization')
          }}</span>
          <FormInput v-model="drafts[provider.type].organization" dir="ltr" />
        </label>

        <label class="admin-ai__field">
          <span class="admin-ai__field-label">{{ $t('adminAI.models') }}</span>
          <FormInput
            v-model="drafts[provider.type].models"
            dir="ltr"
            :placeholder="modelPlaceholder(provider.type)"
          />
          <span class="admin-ai__hint">{{ $t('adminAI.modelsHint') }}</span>
        </label>

        <div class="admin-ai__actions">
          <Button
            type="primary"
            size="small"
            :loading="saving === provider.type"
            :disabled="saving !== null"
          >
            {{ $t('action.save') }}
          </Button>
          <ButtonText
            v-if="isCustomised(provider)"
            type="secondary"
            :disabled="saving !== null"
            @click.prevent="reset(provider)"
          >
            {{ $t('adminAI.reset') }}
          </ButtonText>
          <span v-if="saved === provider.type" class="admin-ai__saved">
            <i class="iconoir-check"></i> {{ $t('adminAI.saved') }}
          </span>
        </div>
      </form>
    </div>

    <p class="admin-ai__disabled">{{ $t('adminAI.mistralDisabled') }}</p>
  </div>
</template>

<script>
import GenerativeAIService from '@jadawel/modules/arabase/services/generativeAI'
import { notifyIf } from '@jadawel/modules/core/utils/error'

// Product names, shown as each provider writes them.
const PROVIDER_NAMES = {
  openai: 'OpenAI',
  anthropic: 'Claude (Anthropic)',
  ollama: 'Ollama',
  openrouter: 'OpenRouter',
}

const MODEL_EXAMPLES = {
  openai: 'gpt-5, gpt-5-mini',
  anthropic: 'claude-sonnet-5, claude-haiku-4-5',
  ollama: 'llama3.3, qwen3',
  openrouter: 'anthropic/claude-sonnet-5, openai/gpt-5',
}

export default {
  name: 'AdminGenerativeAISettings',
  data() {
    return {
      loading: true,
      providers: [],
      drafts: {},
      saving: null,
      saved: null,
    }
  },
  async mounted() {
    try {
      const { data } = await GenerativeAIService(this.$client).fetchProviders()
      this.setProviders(data.providers)
    } catch (error) {
      notifyIf(error, 'settings')
    } finally {
      this.loading = false
    }
  },
  methods: {
    providerName(type) {
      return PROVIDER_NAMES[type] || type
    },
    modelPlaceholder(type) {
      return MODEL_EXAMPLES[type] || ''
    },
    has(provider, field) {
      return provider.fields.includes(field)
    },
    isCustomised(provider) {
      return (
        provider.api_key_set ||
        provider.models.length > 0 ||
        provider.host ||
        provider.base_url ||
        provider.organization
      )
    },
    setProviders(providers) {
      this.providers = providers
      this.drafts = Object.fromEntries(
        providers.map((provider) => [
          provider.type,
          {
            api_key: '',
            host: provider.host,
            base_url: provider.base_url,
            organization: provider.organization,
            models: provider.models.join(', '),
          },
        ])
      )
    },
    async send(provider, request) {
      this.saving = provider.type
      this.saved = null
      try {
        const { data } = await request()
        this.setProviders(data.providers)
        this.saved = provider.type
      } catch (error) {
        notifyIf(error, 'settings')
      } finally {
        this.saving = null
      }
    },
    save(provider) {
      const draft = this.drafts[provider.type]
      const values = {
        models: draft.models
          .split(',')
          .map((model) => model.trim())
          .filter((model) => model),
      }
      for (const field of ['api_key', 'host', 'base_url', 'organization']) {
        if (this.has(provider, field)) {
          values[field] = draft[field]
        }
      }
      return this.send(provider, () =>
        GenerativeAIService(this.$client).updateProvider(provider.type, values)
      )
    },
    clearKey(provider) {
      return this.send(provider, () =>
        GenerativeAIService(this.$client).updateProvider(provider.type, {
          clear_api_key: true,
        })
      )
    },
    reset(provider) {
      return this.send(provider, () =>
        GenerativeAIService(this.$client).resetProvider(provider.type)
      )
    },
  },
}
</script>
