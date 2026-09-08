<template>
  <div class="layout__col-2-scroll">
    <div class="admin-backup">
      <h1>{{ $t('adminBackup.title') }}</h1>
      <p class="admin-backup__description">
        {{ $t('adminBackup.description') }}
      </p>

      <div v-if="loading" class="loading-absolute-center"></div>

      <template v-else>
        <!-- Health first. The question this page exists to answer is "can I
             rely on these right now", and it should be readable without
             interpreting a table. -->
        <div
          class="admin-backup__health"
          :class="`admin-backup__health--${healthLevel}`"
        >
          <i :class="healthIcon" class="admin-backup__health-icon"></i>
          <div>
            <div class="admin-backup__health-title">{{ healthTitle }}</div>
            <div class="admin-backup__health-detail">{{ healthDetail }}</div>
            <ul
              v-if="health.configuration_errors.length"
              class="admin-backup__health-errors"
            >
              <li
                v-for="(error, index) in health.configuration_errors"
                :key="index"
              >
                {{ error }}
              </li>
            </ul>
          </div>
        </div>

        <div class="admin-backup__group">
          <h2 class="admin-backup__group-title">
            {{ $t('adminBackup.scheduleTitle') }}
          </h2>
          <p class="admin-backup__group-description">
            {{ $t('adminBackup.scheduleDescription') }}
          </p>

          <div class="admin-backup__schedule">
            <Dropdown
              :model-value="schedule.frequency"
              :disabled="!enabled || savingFrequency"
              class="admin-backup__frequency"
              @update:model-value="changeFrequency"
            >
              <DropdownItem
                v-for="option in frequencies"
                :key="option"
                :name="$t(`adminBackup.frequency.${option}`)"
                :value="option"
              />
            </Dropdown>
            <span class="admin-backup__next-run">
              <template v-if="health.next_run_on">
                {{
                  $t('adminBackup.nextRun', {
                    when: formatDate(health.next_run_on),
                  })
                }}
              </template>
            </span>
            <Button
              type="secondary"
              :disabled="!enabled || runningNow"
              :loading="runningNow"
              @click="runNow"
            >
              {{ $t('adminBackup.runNow') }}
            </Button>
          </div>
        </div>

        <div class="admin-backup__group">
          <h2 class="admin-backup__group-title">
            {{ $t('adminBackup.historyTitle') }}
          </h2>
          <p class="admin-backup__group-description">
            {{ $t('adminBackup.historyDescription') }}
          </p>

          <p v-if="runs.length === 0" class="admin-backup__empty">
            {{ $t('adminBackup.noRuns') }}
          </p>

          <div v-else class="admin-backup__table-wrapper">
            <table class="admin-backup__table">
              <thead>
                <tr>
                  <th>{{ $t('adminBackup.column.started') }}</th>
                  <th>{{ $t('adminBackup.column.status') }}</th>
                  <th>{{ $t('adminBackup.column.trigger') }}</th>
                  <th>{{ $t('adminBackup.column.size') }}</th>
                  <th>{{ $t('adminBackup.column.duration') }}</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="run in runs" :key="run.id">
                  <td>{{ formatDate(run.started_on) }}</td>
                  <td>
                    <span
                      class="admin-backup__status"
                      :class="`admin-backup__status--${run.status}`"
                    >
                      {{ $t(`adminBackup.status.${run.status}`) }}
                    </span>
                    <div v-if="run.error" class="admin-backup__error">
                      {{ run.error }}
                    </div>
                  </td>
                  <td>{{ $t(`adminBackup.trigger.${run.trigger}`) }}</td>
                  <td>{{ formatSize(run) }}</td>
                  <td>{{ formatDuration(run.duration_seconds) }}</td>
                  <td>
                    <Button
                      v-if="run.status === 'success'"
                      type="secondary"
                      size="small"
                      @click="openRestore(run)"
                    >
                      {{ $t('adminBackup.restore') }}
                    </Button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </template>

      <AdminBackupRestoreModal ref="restoreModal" :run="restoringRun" />
    </div>
  </div>
</template>

<script setup>
definePageMeta({
  layout: 'app',
  middleware: 'staff',
})
</script>

<script>
import AdminBackupRestoreModal from '@jadawel/modules/arabase/components/AdminBackupRestoreModal'
import BackupService from '@jadawel/modules/arabase/services/backup'
import moment from '@jadawel/modules/core/moment'
import { notifyIf } from '@jadawel/modules/core/utils/error'

export default {
  name: 'AdminBackup',
  components: { AdminBackupRestoreModal },
  data() {
    return {
      loading: true,
      enabled: false,
      schedule: { frequency: 'daily', crontab: '' },
      health: {
        status: 'disabled',
        healthy: false,
        last_success_on: null,
        next_run_on: null,
        configuration_errors: [],
        last_run: null,
      },
      runs: [],
      savingFrequency: false,
      runningNow: false,
      restoringRun: null,
      frequencies: ['hourly', 'daily', 'weekly'],
    }
  },
  computed: {
    /**
     * `disabled` is deliberately not an error: switched off on purpose is a
     * legitimate state. `misconfigured` is, because the job is scheduled and
     * will fail every time it fires.
     */
    healthLevel() {
      return {
        ok: 'ok',
        disabled: 'neutral',
        misconfigured: 'error',
        never_run: 'warning',
        last_failed: 'error',
        overdue: 'error',
      }[this.health.status]
    },
    healthIcon() {
      return {
        ok: 'iconoir-check-circle',
        neutral: 'iconoir-pause',
        warning: 'iconoir-warning-triangle',
        error: 'iconoir-warning-circle',
      }[this.healthLevel]
    },
    healthTitle() {
      return this.$t(`adminBackup.health.${this.health.status}.title`)
    },
    healthDetail() {
      const last = this.health.last_success_on
      return this.$t(`adminBackup.health.${this.health.status}.detail`, {
        when: last ? this.formatDate(last) : '',
      })
    },
  },
  async mounted() {
    await this.load()
  },
  methods: {
    async load() {
      this.loading = true
      try {
        const service = BackupService(this.$client)
        const [overview, runs] = await Promise.all([
          service.fetchOverview(),
          service.fetchRuns(),
        ])
        this.applyOverview(overview.data)
        this.runs = runs.data
      } catch (error) {
        notifyIf(error, 'settings')
      }
      this.loading = false
    },
    applyOverview(data) {
      this.enabled = data.enabled
      this.schedule = data.schedule
      this.health = data.health
    },
    async changeFrequency(frequency) {
      this.savingFrequency = true
      try {
        const { data } = await BackupService(this.$client).setFrequency(
          frequency
        )
        this.applyOverview(data)
      } catch (error) {
        notifyIf(error, 'settings')
      }
      this.savingFrequency = false
    },
    async runNow() {
      this.runningNow = true
      try {
        await BackupService(this.$client).runNow()
        // The run is queued, not finished, so the row appears as `running`.
        await this.load()
      } catch (error) {
        notifyIf(error, 'settings')
      }
      this.runningNow = false
    },
    openRestore(run) {
      this.restoringRun = run
      this.$refs.restoreModal.show()
    },
    formatDate(value) {
      return value ? moment(value).format('LLL') : ''
    },
    formatDuration(seconds) {
      if (seconds === null || seconds === undefined) {
        return '—'
      }
      if (seconds < 60) {
        return this.$t('adminBackup.seconds', { count: Math.round(seconds) })
      }
      return this.$t('adminBackup.minutes', { count: Math.round(seconds / 60) })
    },
    formatSize(run) {
      const total = (run.size_bytes || 0) + (run.media_size_bytes || 0)
      if (total === 0) {
        return '—'
      }
      const mb = total / (1024 * 1024)
      return mb < 1024 ? `${mb.toFixed(1)} MB` : `${(mb / 1024).toFixed(2)} GB`
    },
  },
}
</script>
