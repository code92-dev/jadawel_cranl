#!/usr/bin/env bash
set -Eeo pipefail

# A fresh database must migrate and import the 36 bundled templates before it is
# ready, which on a GitHub runner takes several minutes (six templates needed up to
# three). Allow fifteen minutes while still polling every second and failing
# immediately after the bounded window.

# Keep in sync with arabase.template_catalog.LOCAL_TEMPLATE_CATALOG. Production
# startup is not complete until the fork's authoritative local-only catalog is live.
LOCAL_APPLICATION_TEMPLATES=(
  "arabic-performance-review"
  "arabic-project-management"
  "saudi-budget-consolidation"
  "performance-reviews"
  "project-management-en"
  "saudi-budget-consolidation-en"
  "saudi-restaurant-management"
  "saudi-business-expenses"
  "saudi-employee-onboarding"
  "saudi-school-management"
  "saudi-nonprofit-management"
  "saudi-inspections-compliance"
  "saudi-intake-qualification"
  "saudi-work-management"
  "saudi-password-reset"
  "saudi-leave-management"
  "saudi-compliance-assessment"
  "saudi-property-management"
  "saudi-order-kiosk"
  "saudi-crm"
  "saudi-purchase-orders"
  "saudi-restaurant-management-en"
  "saudi-business-expenses-en"
  "saudi-employee-onboarding-en"
  "saudi-school-management-en"
  "saudi-nonprofit-management-en"
  "saudi-inspections-compliance-en"
  "saudi-intake-qualification-en"
  "saudi-work-management-en"
  "saudi-password-reset-en"
  "saudi-leave-management-en"
  "saudi-compliance-assessment-en"
  "saudi-property-management-en"
  "saudi-order-kiosk-en"
  "saudi-crm-en"
  "saudi-purchase-orders-en"
)

jadawel_ready() {
    curlf() {
      HTTP_CODE=$(curl --silent -o /dev/null --write-out "%{http_code}" --max-time 10 "$@")
      if [[ ${HTTP_CODE} -lt 200 || ${HTTP_CODE} -gt 299 ]] ; then
        echo "$1 not ready..."
        return 22
      fi
      return 0
    }

    templates_ready(){
      TEMPLATES_JSON=$(curl --silent --max-time 10 "${PUBLIC_BACKEND_URL:-http://backend:8000}/api/templates/")
      for template in "${LOCAL_APPLICATION_TEMPLATES[@]}"; do
        if [[ ${TEMPLATES_JSON} != *"$template"* ]] ; then
          echo "Template $template is missing..."
          return 22
        fi
      done
      return 0
    }

    if curlf "${PUBLIC_WEB_FRONTEND_URL:-http://web-frontend:3000}/_health/" && curlf "${PUBLIC_BACKEND_URL:-http://backend:8000}/api/_health/" && templates_ready; then
      return 0
    else
      return 1
    fi
}

for _ in $(seq 1 "${JADAWEL_E2E_STARTUP_MAX_WAIT_TIME_SECONDS:-900}")
do
  echo 'Waiting for backend, web-frontend and synced templates to be ready'
  if jadawel_ready; then
    echo 'Jadawel is ready! Exiting with success code.'
    exit 0
  fi
  sleep 1
done
echo 'E2E services failed to startup in time, crashing the test.'
if command -v docker >/dev/null 2>&1; then
  for service in e2e-backend e2e-frontend e2e-celery; do
    echo "=== ${service} logs ==="
    docker logs --tail 200 "${service}" 2>&1 || true
  done
fi
exit 1
