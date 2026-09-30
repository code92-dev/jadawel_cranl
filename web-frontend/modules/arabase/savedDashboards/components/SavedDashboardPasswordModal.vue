<template>
  <Modal ref="modal" :small="true" @hidden="reset">
    <h2 class="box__title">{{ $t('myDashboards.passwordTitle') }}</h2>
    <p class="box__description">
      {{ $t('myDashboards.passwordChanged', { name: cardTitle }) }}
    </p>
    <Error :error="error"></Error>
    <form @submit.prevent="submit">
      <FormGroup :label="$t('myDashboards.passwordLabel')" required>
        <FormInput
          v-model="password"
          type="password"
          autocomplete="off"
          :disabled="loading"
        />
      </FormGroup>
      <div class="actions">
        <ul class="action__links">
          <li>
            <a :disabled="loading" @click.prevent="hide()">{{
              $t('action.cancel')
            }}</a>
          </li>
        </ul>
        <Button
          type="primary"
          :loading="loading"
          :disabled="loading || !password"
        >
          {{ $t('myDashboards.unlock') }}
        </Button>
      </div>
    </form>
  </Modal>
</template>

<script>
import modal from '@jadawel/modules/core/mixins/modal'
import error from '@jadawel/modules/core/mixins/error'
import SavedDashboardsService from '@jadawel/modules/arabase/services/savedDashboards'
import { showSavedDashboardError } from '@jadawel/modules/arabase/savedDashboards/errors'

/**
 * Asks again for a saved link's password after its owner changed it. The
 * password is checked by the server and, for another server's link, kept
 * sealed there; the browser never stores it.
 */
export default {
  name: 'SavedDashboardPasswordModal',
  mixins: [modal, error],
  emits: ['unlocked'],
  data() {
    return { card: null, password: '', loading: false }
  },
  computed: {
    cardTitle() {
      return this.card?.title || this.$t('myDashboards.untitled')
    },
  },
  methods: {
    open(card) {
      this.card = card
      this.show()
    },
    reset() {
      this.password = ''
      this.hideError()
    },
    async submit() {
      if (!this.password || this.loading) {
        return
      }
      this.loading = true
      this.hideError()
      try {
        const { data } = await SavedDashboardsService(
          this.$client
        ).enterPassword(this.card.id, this.password)
        this.$emit('unlocked', data)
        this.hide()
      } catch (error) {
        showSavedDashboardError(this, error)
      } finally {
        this.loading = false
      }
    },
  },
}
</script>
