/**
 * Opens Sanad with a request already typed for the user to finish.
 *
 * The right sidebar only mounts Sanad's panel once it opens, so an event alone
 * would be missed the first time: the text is also parked here, and the panel
 * takes it when it mounts. Whichever arrives first consumes it.
 */
let pendingDraft = null

export function askSanad(bus, text) {
  pendingDraft = text
  bus.$emit('toggle-right-sidebar', true)
  bus.$emit('sanad-draft', text)
}

export function takeSanadDraft() {
  const text = pendingDraft
  pendingDraft = null
  return text
}
