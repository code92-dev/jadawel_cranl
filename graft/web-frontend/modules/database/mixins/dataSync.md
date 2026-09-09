# web-frontend/modules/database/mixins/dataSync.js

- data · method · L8-L17 — data()
- beforeUnmount · method · L18-L20 — beforeUnmount()
- orderedProperties · method · L22-L37 — orderedProperties()
- toggleVisibleField · method · L40-L47 — toggleVisibleField(key)
- getFieldTypeIconClass · method · L48-L50 — getFieldTypeIconClass(fieldType)
- fetchExistingProperties · method · L51-L73 — async fetchExistingProperties(table)
- fetchNonExistingProperties · method · L74-L102 — async fetchNonExistingProperties(type, values)
- syncTable · method · L103-L122 — async syncTable(table)
- update · method · L123-L152 — async update(table, values, syncTable = true)
- onJobFailed · method · L153-L159 — onJobFailed()
- onJobPollingError · method · L160-L162 — onJobPollingError(error)
- stopPollAndHandleError · method · L163-L166 — stopPollAndHandleError(error)
