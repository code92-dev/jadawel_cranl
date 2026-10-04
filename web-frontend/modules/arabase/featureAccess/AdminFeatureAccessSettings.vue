<template>
  <div id="feature-access" class="admin-settings__group feature-access">
    <h2 class="admin-settings__group-title">
      {{ $t('adminFeatureAccess.title') }}
    </h2>
    <p class="feature-access__intro">
      {{ $t('adminFeatureAccess.description') }}
    </p>

    <div v-if="loading" class="loading"></div>

    <div
      v-for="item in features"
      v-else
      :key="item.feature"
      class="admin-settings__item feature-access__feature"
    >
      <div class="admin-settings__label">
        <div class="admin-settings__name">
          {{ $t(`adminFeatureAccess.features.${item.feature}.name`) }}
        </div>
        <div class="admin-settings__description">
          {{ $t(`adminFeatureAccess.features.${item.feature}.description`) }}
        </div>
      </div>

      <div class="admin-settings__control feature-access__control">
        <SwitchInput
          :value="item.everyone"
          :disabled="busy !== null"
          @input="setEveryone(item, $event)"
          >{{ $t('adminFeatureAccess.everyone') }}</SwitchInput
        >

        <p v-if="item.everyone" class="feature-access__note">
          {{ $t('adminFeatureAccess.everyoneNote') }}
        </p>

        <template v-else>
          <div class="feature-access__label">
            {{ $t('adminFeatureAccess.invited') }}
          </div>
          <p v-if="!item.grants.length" class="feature-access__note">
            {{ $t('adminFeatureAccess.noInvited') }}
          </p>
          <ul v-else class="feature-access__grants">
            <li
              v-for="grant in item.grants"
              :key="grant.id"
              class="feature-access__grant"
            >
              <!-- The lines follow the page's direction; each value is
                   isolated, so an address stays LTR inside an Arabic row. -->
              <div class="feature-access__identity">
                <span class="feature-access__email"
                  ><bdi dir="ltr">{{ grant.email }}</bdi></span
                >
                <span
                  v-if="grant.user && grant.user.name"
                  class="feature-access__name"
                  ><bdi>{{ grant.user.name }}</bdi></span
                >
              </div>
              <Badge v-if="!grant.user" color="yellow" size="small" rounded>{{
                $t('adminFeatureAccess.noAccount')
              }}</Badge>
              <Badge
                v-else-if="!grant.user.is_active"
                color="neutral"
                size="small"
                rounded
                >{{ $t('adminFeatureAccess.deactivated') }}</Badge
              >
              <ButtonIcon
                icon="iconoir-cancel"
                type="secondary"
                size="small"
                class="feature-access__remove"
                :disabled="busy !== null"
                :title="$t('adminFeatureAccess.remove', { email: grant.email })"
                :aria-label="
                  $t('adminFeatureAccess.remove', { email: grant.email })
                "
                @click="remove(item, grant)"
              />
            </li>
          </ul>

          <form class="feature-access__invite" @submit.prevent="invite(item)">
            <FormInput
              v-model="drafts[item.feature]"
              dir="ltr"
              autocomplete="off"
              :aria-label="$t('adminFeatureAccess.emails')"
              :placeholder="$t('adminFeatureAccess.emailsPlaceholder')"
              :error="Boolean(invalid[item.feature])"
            />
            <Button
              type="primary"
              size="regular"
              :loading="busy === item.feature"
              :disabled="busy !== null || !drafts[item.feature].trim()"
            >
              {{ $t('adminFeatureAccess.invite') }}
            </Button>
          </form>
          <p
            v-if="invalid[item.feature]"
            class="feature-access__error"
            role="alert"
          >
            {{
              $t('adminFeatureAccess.invalidEmails', {
                emails: invalid[item.feature],
              })
            }}
          </p>
          <p class="feature-access__hint">
            {{ $t('adminFeatureAccess.emailsHint') }}
          </p>
        </template>
      </div>
    </div>
  </div>
</template>

<script>
import FeatureAccessService from '@jadawel/modules/arabase/services/featureAccess'
import { FEATURES } from '@jadawel/modules/arabase/featureAccess/featureAccess'
import { notifyIf } from '@jadawel/modules/core/utils/error'

// Deliberately loose: the backend validates each address properly, this only
// names the obvious typos before a round trip.
const EMAIL = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

export function parseEmails(text) {
  return [
    ...new Set(
      text
        .split(/[\s,;،]+/)
        .map((email) => email.trim())
        .filter((email) => email)
    ),
  ]
}

export default {
  name: 'AdminFeatureAccessSettings',
  data() {
    return {
      loading: true,
      features: [],
      drafts: Object.fromEntries(FEATURES.map((feature) => [feature, ''])),
      invalid: {},
      busy: null,
    }
  },
  async mounted() {
    try {
      const { data } = await FeatureAccessService(this.$client).fetchAll()
      this.features = data.features
    } catch (error) {
      notifyIf(error, 'settings')
    } finally {
      this.loading = false
    }
  },
  methods: {
    async send(item, request) {
      this.busy = item.feature
      try {
        const { data } = await request()
        this.features = data.features
        return true
      } catch (error) {
        notifyIf(error, 'settings')
        return false
      } finally {
        this.busy = null
      }
    },
    setEveryone(item, everyone) {
      return this.send(item, () =>
        FeatureAccessService(this.$client).setEveryone(item.feature, everyone)
      )
    },
    async invite(item) {
      const emails = parseEmails(this.drafts[item.feature])
      const invalid = emails.filter((email) => !EMAIL.test(email))
      this.invalid = { ...this.invalid, [item.feature]: invalid.join(', ') }
      if (invalid.length || !emails.length) {
        return
      }
      const added = await this.send(item, () =>
        FeatureAccessService(this.$client).addGrants(item.feature, emails)
      )
      if (added) {
        this.drafts[item.feature] = ''
      }
    },
    remove(item, grant) {
      return this.send(item, () =>
        FeatureAccessService(this.$client).removeGrant(item.feature, grant.id)
      )
    },
  },
}
</script>
