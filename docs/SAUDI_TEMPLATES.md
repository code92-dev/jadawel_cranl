# Saudi template editions

Fifteen upstream templates ship in Saudi editions, each in Arabic (`قوالب عربية`)
and English (`English Templates`). The template picker lists them next to the
fork's own three; `backend/src/arabase/template_catalog.py` (`SAUDI_EDITIONS`)
is the authoritative list. `tools/saudi_templates/` builds them from the
upstream JSON; its README explains how.

Every edition carries Saudi sample data: Saudi names, Saudi mobile numbers
(`+966 5x`), riyal amounts, Saudi cities and districts, Sunday-to-Thursday
working weeks and local organisations. Builder apps lay out right to left in
Arabic and left to right in English.

## Databases

| Slug | From | What changed |
|---|---|---|
| `saudi-restaurant-management` | Restaurant Management | Saudi dishes (kabsa, mandi, mutabbaq, maqluba), no alcohol (beverages instead), SFDA and Balady certificates, prices in riyals |
| `saudi-business-expenses` | Business Expenses | Expense types rewritten for Zakat and income tax, GOSI, government fees and HADAF; VAT (15%) formula on expenses; suppliers' VAT numbers |
| `saudi-employee-onboarding` | New Hire Onboarding | Qiwa contract, GOSI registration, Mudad wage protection, national ID or iqama, NCA-aligned security policies; father's name instead of a middle initial |
| `saudi-school-management` | Elementary School Management | Saudi curriculum (لغتي، الدراسات الإسلامية، المهارات الرقمية…), Ministry of Education textbooks, grades through intermediate 2, birth dates that fit each grade |
| `saudi-nonprofit-management` | Non-profit Organization Management | Jeddah charity, Ramadan iftar for donors, Ehsan donations, National Center for Non-Profit Sector, grants in riyals |

## Automations

| Slug | From | What changed |
|---|---|---|
| `saudi-inspections-compliance` | Inspections & Compliance | The Slack alert is an email to the inspector |
| `saudi-intake-qualification` | Intake & Qualification Engine | Urgent leads email the sales team instead of Slack; budget ranges in riyals |
| `saudi-work-management` | Work Management Platform | NCA ECC compliance and Ramadan campaign projects; the webhook workflow reads the translated field names |
| `saudi-password-reset` | Password reset | Arabic right-to-left reset email and pages |
| `saudi-leave-management` | OOO Management | Saudi Labor Law leave types and 21/30-day entitlements, Friday–Saturday weekend and 2024 public holidays, and a new automation: notify the approver, notify the employee of the decision, weekly reminder to HR while requests are pending |

The automations start as drafts. Configure the SMTP integration (and the
database webhook for the work-management status workflow) before enabling them.

## Applications

| Slug | From | What changed |
|---|---|---|
| `saudi-compliance-assessment` | Compliance Assessment Builder | Assessments for the NCA Essential Cybersecurity Controls, the Personal Data Protection Law, ZATCA e-invoicing, the Anti-Harassment Law and vendor Zakat/VAT checks |
| `saudi-property-management` | Commercial Property Management | Towers in Riyadh, Jeddah and Dammam, Ejar contract numbers, Saudi postal codes, local tenants and contractors |
| `saudi-order-kiosk` | Order Kiosk | Juice bar with sobia, tahini and Sidr honey; prices in riyals |
| `saudi-crm` | Lightweight CRM | Saudi companies, contacts and pipelines; contract values in riyals |
| `saudi-purchase-orders` | Purchase Order Management | Suppliers in Saudi industrial cities, VAT (15%) and total-with-VAT on approved lines, suppliers' VAT number and local content share |

## Notes

- Sample identifiers (VAT numbers, Ejar numbers, phone numbers) have the right
  shape but are made up.
- Calendar dates stay in the upstream years; the leave calendar is 2024, so its
  holidays are 2024's.
- The catalog imports every bundled template as a preview workspace after
  migrations. Thirty more templates lengthen the first start after this release.
