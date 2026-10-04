/**
 * The features an administrator opens to every user or to invited email
 * addresses (docs/FEATURE_ACCESS.md). The values match the backend's
 * `arabase.feature_access.models.Feature`.
 */
export const FEATURES = ['automation', 'builder', 'sanad']

/**
 * Whether the signed-in user may use a gated feature. The login response
 * carries the answer under `arabase_features`, and the `user_data_updated`
 * realtime event keeps it current; without it, staff keep the feature.
 */
export function hasFeature(store, feature) {
  const features = store.getters['auth/getAdditionalUserData']?.arabase_features
  if (features && feature in features) {
    return Boolean(features[feature])
  }
  return store.getters['auth/isStaff']
}
