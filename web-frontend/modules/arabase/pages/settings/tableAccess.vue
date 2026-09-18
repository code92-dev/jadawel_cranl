<template>
  <div class="table-access">
    <p class="table-access__description">
      {{ $t('tableAccess.description') }}
    </p>

    <form class="table-access__invite" @submit.prevent="invite">
      <FormGroup
        :label="$t('tableAccess.email')"
        :error="!!emailError"
        :helper-text="emailError"
        required
        small-label
      >
        <FormInput
          v-model="form.email"
          type="email"
          dir="ltr"
          size="large"
          :placeholder="$t('tableAccess.emailPlaceholder')"
        />
      </FormGroup>

      <FormGroup :label="$t('tableAccess.tables')" required small-label>
        <p v-if="!tables.length" class="table-access__empty">
          {{ $t('tableAccess.noTables') }}
        </p>
        <ul v-else class="table-access__table-list">
          <li v-for="table in tables" :key="table.id">
            <Checkbox
              :checked="isSelected(table.id)"
              @input="toggleTable(table.id)"
            >
              <span class="table-access__table-name">
                <bdi>{{ table.databaseName }}</bdi>
                <span class="table-access__separator">/</span>
                <bdi>{{ table.name }}</bdi>
              </span>
            </Checkbox>
            <!-- `fixed-items` positions the item list fixed so it escapes the
                 scrollable table list above; `show-search` off because two
                 options do not need a search box. -->
            <Dropdown
              v-if="isSelected(table.id)"
              :value="levelOf(table.id)"
              :show-search="false"
              fixed-items
              class="table-access__level"
              @input="setLevel(table.id, $event)"
            >
              <DropdownItem
                v-for="level in levels"
                :key="level"
                :name="$t(`tableAccess.levels.${level}`)"
                :value="level"
              />
            </Dropdown>
          </li>
        </ul>
      </FormGroup>

      <Button
        type="primary"
        size="large"
        button-type="submit"
        :loading="inviting"
        :disabled="inviting || !form.tables.length || !form.email"
      >
        {{ $t('tableAccess.invite') }}
      </Button>
    </form>

    <Alert v-if="error" type="error">
      {{ $t('tableAccess.error') }}
      <span v-if="errorDetail" dir="auto">— {{ errorDetail }}</span>
    </Alert>

    <div v-if="loading" class="loading-absolute-center"></div>

    <template v-else>
      <h2 class="table-access__heading">{{ $t('tableAccess.guests') }}</h2>
      <p v-if="!guests.length" class="table-access__empty">
        {{ $t('tableAccess.noGuests') }}
      </p>
      <ul v-else class="table-access__guests">
        <li v-for="guest in guests" :key="guest.workspace_user_id">
          <div class="table-access__guest-identity">
            <strong>{{ guest.name || guest.email }}</strong>
            <bdi class="table-access__guest-email">{{ guest.email }}</bdi>
          </div>
          <ul class="table-access__guest-tables">
            <li v-for="table in guest.tables" :key="table.table_id">
              <bdi>{{ table.name }}</bdi>
              <span class="table-access__badge">
                {{ $t(`tableAccess.levels.${table.level}`) }}
              </span>
            </li>
          </ul>
          <Button
            type="danger"
            size="small"
            :disabled="busy"
            @click="revoke(guest)"
          >
            {{ $t('tableAccess.revoke') }}
          </Button>
        </li>
      </ul>

      <h2 class="table-access__heading">{{ $t('tableAccess.pending') }}</h2>
      <p v-if="!invitations.length" class="table-access__empty">
        {{ $t('tableAccess.noPending') }}
      </p>
      <ul v-else class="table-access__guests">
        <li v-for="invitation in invitations" :key="invitation.id">
          <div class="table-access__guest-identity">
            <bdi>{{ invitation.email }}</bdi>
          </div>
          <ul class="table-access__guest-tables">
            <li v-for="table in invitation.tables" :key="table.table_id">
              <bdi>{{ table.name }}</bdi>
              <span class="table-access__badge">
                {{ $t(`tableAccess.levels.${table.level}`) }}
              </span>
            </li>
          </ul>
        </li>
      </ul>
    </template>
  </div>
</template>

<script>
import TableAccessService from '@jadawel/modules/arabase/services/tableAccess'
import { DatabaseApplicationType } from '@jadawel/modules/database/applicationTypes'
import { describeApiError } from '@jadawel/modules/arabase/utils/apiError'

const LEVELS = ['VIEWER', 'EDITOR']

export default {
  name: 'TableAccessSettings',
  props: {
    workspace: {
      type: Object,
      required: true,
    },
  },
  data() {
    return {
      levels: LEVELS,
      loading: true,
      inviting: false,
      busy: false,
      error: false,
      errorDetail: '',
      emailError: '',
      guests: [],
      invitations: [],
      form: { email: '', tables: [] },
    }
  },
  computed: {
    /** Every table of the workspace, flattened with its database name. */
    tables() {
      return this.$store.getters['application/getAllOfWorkspace'](
        this.workspace
      )
        .filter(
          (application) =>
            application.type === DatabaseApplicationType.getType()
        )
        .flatMap((database) =>
          (database.tables || []).map((table) => ({
            id: table.id,
            name: table.name,
            databaseName: database.name,
          }))
        )
    },
  },
  async mounted() {
    await this.load()
  },
  methods: {
    isSelected(tableId) {
      return this.form.tables.some((entry) => entry.table_id === tableId)
    },
    levelOf(tableId) {
      const entry = this.form.tables.find((item) => item.table_id === tableId)
      return entry ? entry.level : LEVELS[0]
    },
    toggleTable(tableId) {
      if (this.isSelected(tableId)) {
        this.form.tables = this.form.tables.filter(
          (entry) => entry.table_id !== tableId
        )
      } else {
        this.form.tables.push({ table_id: tableId, level: LEVELS[0] })
      }
    },
    setLevel(tableId, level) {
      const entry = this.form.tables.find((item) => item.table_id === tableId)
      if (entry) {
        entry.level = level
      }
    },
    fail(error) {
      this.error = true
      this.errorDetail = describeApiError(error)
    },
    async load() {
      this.loading = true
      this.error = false
      this.errorDetail = ''
      try {
        const { data } = await TableAccessService(this.$client).fetchAll(
          this.workspace.id
        )
        this.guests = data.guests
        this.invitations = data.invitations
      } catch (error) {
        this.fail(error)
      } finally {
        this.loading = false
      }
    },
    async invite() {
      this.inviting = true
      this.error = false
      this.errorDetail = ''
      this.emailError = ''
      try {
        await TableAccessService(this.$client).invite(this.workspace.id, {
          email: this.form.email,
          tables: this.form.tables,
          // The accept page is core's, so the base URL is the one a normal
          // workspace invitation uses.
          baseUrl: `${this.$config.public.jadawelEmbeddedShareUrl}/workspace-invitation`,
        })
        this.form = { email: '', tables: [] }
        await this.load()
      } catch (error) {
        this.fail(error)
      } finally {
        this.inviting = false
      }
    },
    async revoke(guest) {
      this.busy = true
      this.error = false
      this.errorDetail = ''
      try {
        await TableAccessService(this.$client).revoke(
          this.workspace.id,
          guest.workspace_user_id
        )
        await this.load()
      } catch (error) {
        this.fail(error)
      } finally {
        this.busy = false
      }
    },
  },
}
</script>
