# Arabic Terminology Glossary — Jadawel (جداول)

Single source of truth for how Jadawel/Jadawel product terms are translated into
Arabic. **Every `ar.json` translation must use these exact terms** so the UI reads
consistently. When you introduce a new recurring term, add it here first.

Arabic is the **primary** locale; keep translations natural for a Saudi business/
government audience (Modern Standard Arabic, no transliteration where a real Arabic
term exists).

## Core product nouns

### Billing and organizations

| English | Arabic | Notes |
| --- | --- | --- |
| Billing | الفوترة | Subscription and payment management. |
| Billing account | حساب الفوترة | Individual or organization payer context. |
| Subscription | اشتراك | Recurring access period. |
| Plan | باقة | Product subscription offering. |
| Organization | منظمة | Company or organization account. |
| Complimentary access | وصول مجاني | Explicit administrator grant. |
| Seat | مقعد | One licensed organization member. |
| Activity log | سجل النشاط | Chronological record of organization and billing actions. |
| Payment provider | مزود الدفع | External service such as Moyasar that processes payments. |
| Provider health | حالة مزود الدفع | Safe configuration and reachability status. |
| External payment | دفعة خارجية | Administrator-recorded settlement outside the payment provider. |
| Payment history | سجل المدفوعات | Chronological list of payment orders and their outcomes. |

### Workspace vocabulary

| English | Arabic | Notes |
|---------|--------|-------|
| Jadawel (product) | جداول | Product name; never translated further. |
| Workspace | مساحة عمل | pl. مساحات عمل |
| Application / Database | قاعدة بيانات | An application in a workspace. |
| Table | جدول | pl. جداول (same as product name — fine in context). |
| View | عرض | pl. عروض. Grid/Gallery/Form/Kanban/Calendar are types of عرض. |
| Field | حقل | pl. حقول. A column definition. |
| Column | عمود | Use حقل for the data model, عمود for the visual grid column. |
| Row | صف | pl. صفوف. |
| Record | سجل | Prefer صف in grid contexts; سجل for the expanded record modal. |
| Cell | خلية | |
| Primary field | الحقل الأساسي | |
| Dashboard | لوحة التحكم | |
| Widget | عنصر | Dashboard widget. |
| Size | الحجم | Widget size on the dashboard grid, in columns × rows. |
| Key number (widget) | رقم رئيسي | The `summary` widget: one headline number. |
| Goal gauge | مقياس الهدف | The progress widget's half-dial style. |
| Section heading (widget) | عنوان قسم | A text widget that splits a dashboard into parts. |
| Note (widget) | ملاحظة | A text widget explaining how to read a dashboard. |
| Callout (widget) | إبراز | A tinted text widget for what needs attention. |
| Accent colour | اللون المميّز | A widget's colour in its appearance settings. |
| Saudi riyal sign | رمز الريال السعودي | U+20C1. Dashboards draw it in place of ر.س, to the left of the amount. |
| Horizontal bar chart | مخطط أعمدة أفقي | |
| Area chart | مخطط مساحي | |
| On track / At risk / Target met | على المسار / متعثّر / تحقّق الهدف | Progress status labels. |
| Trash | سلة المهملات | |
| Snapshot | لقطة | pl. لقطات |
| Member | عضو | pl. الأعضاء |
| Guest | ضيف | pl. الضيوف. A workspace member limited to specific tables. |
| Table access | وصول الجداول | The settings tab that grants guests specific tables. |
| Viewer (table level) | مُشاهد | Reads a granted table; see also the workspace VIEWER role. |
| Editor (table level) | محرِّر | Reads and edits the rows of a granted table, never its structure. |
| Template | قالب | pl. قوالب |
| Webhook | خطاف ويب | pl. خطافات الويب |
| Automation | أتمتة | |
| Notification | إشعار | pl. الإشعارات |

## View types

| English | Arabic |
|---------|--------|
| Grid | شبكة |
| Gallery | معرض |
| Form | نموذج |
| Kanban | كانبان |
| Calendar | تقويم |
| Timeline | خط زمني |
| Page | صفحة |

## Row coloring

| English | Arabic |
|---------|--------|
| Row coloring | تلوين الصفوف |
| Background color | لون الخلفية |
| Left border color | لون الحد الجانبي |
| Conditions | شروط |
| Rule | قاعدة |
| Default color | اللون الافتراضي |

## Common field types

| English | Arabic |
|---------|--------|
| Single line text | نص من سطر واحد |
| Long text | نص طويل |
| Number | رقم |
| Rating | تقييم |
| Boolean / Checkbox | مربع اختيار |
| Date | تاريخ |
| Single select | اختيار مفرد |
| Multiple select | اختيار متعدد |
| Link to table | ربط بجدول |
| File | ملف |
| Formula | صيغة |
| Phone number | رقم هاتف |
| URL | رابط |
| Email | بريد إلكتروني |
| Duration | مدة |

## Spreadsheets and files

Terms introduced by the Excel/ODS import and export features. Keep "Excel",
"ODS", "XLSX" and "CSV" Latin as technical format tokens.

| English | Arabic |
|---------|--------|
| Spreadsheet | جدول بيانات |
| Sheet | ورقة |
| Workbook | مصنّف جداول |
| Row | صف |
| Column | عمود |

## Builder menu variants

| English | Arabic |
|---------|--------|
| Expanded | موسّع |
| Compact | مضغوط |

## Formulas

| English | Arabic | Notes |
|---------|--------|-------|
| Utility | أداة مساعدة | Formula function category for general-purpose helpers (`range`, `to_json`, `from_json`, `null`). |
| Duration format | تنسيق المدة | Token string such as `d h:mm`; keep tokens Latin. |
| Datetime format | تنسيق التاريخ والوقت | Token string such as `DD/MM/YYYY`; keep tokens Latin. |
| Thousand separator | فاصل الآلاف | |
| Decimal separator | فاصل العشريات | |

## MCP data protection

| English | Arabic | Notes |
|---------|--------|-------|
| Protected field | حقل محمي | A field whose non-empty values are replaced with mask tokens at its MCP endpoint boundary. Do not use حقل مشفّر. |
| Endpoint protection policy | سياسة حماية الحقول | The protected fields selected for one MCP endpoint. |
| Mask token | رمز إخفاء | An opaque reference returned through MCP instead of a protected value. |
| Protected derivative | مشتق محمي | A value that would reproduce or expose information from a protected field. |
| Fingerprint key | مفتاح البصمة | The server-side HMAC key that binds a mask token to the cell value it replaced. Derived from `SECRET_KEY` unless an operator configures a keyring; never user data. |

## Application builder and automation

Terms core's builder and automation modules already use; recorded here because
Sanad's tool labels and skills repeat them.

| English | Arabic | Notes |
|---------|--------|-------|
| Element (builder) | عنصر | pl. عناصر. A piece of an application page (heading, table, form…). Same word as a dashboard Widget; the surrounding screen tells them apart. |
| Theme (application) | سمة | An application's colours, fonts and styles. The user's interface theme is also سمة. |
| Data source | مصدر البيانات | What feeds a page element or widget with rows. |
| Ready-made theme | سمة جاهزة | A theme preset of an application: Jadawel (جداول), Ocean (محيط), Heritage (تراث), Sand (رمال), Stone (حجر). |
| Content language | لغة المحتوى | The language an application's pages are written in; sets alignment and direction. |
| Direction (page) | الاتجاه | Automatic (تلقائي), Right to left (من اليمين إلى اليسار), Left to right (من اليسار إلى اليمين). |
| Box style | نمط الصندوق | A container's quick style: Plain (بدون), Card (بطاقة), Tinted (ملوّن), Outlined (بإطار). |
| Workflow | سير العمل | One automation flow: a trigger followed by its steps. |
| Step (automation) | خطوة | One action of a workflow: "Step 2 of 4" is الخطوة 2 من 4. |
| Trigger / starting event | حدث البدء | What starts a workflow. The periodic one is جدول زمني, never الزناد. |
| Recipe (automation) | وصفة جاهزة | A ready-made workflow built in one click from the start screen. |
| Needs setup | تحتاج إعدادًا | A step whose settings are still incomplete. |

## Sanad AI assistant

| English | Arabic | Notes |
|---------|--------|-------|
| Sanad | سند | Product name of the in-app AI assistant. Never translated; in English UI it reads "Sanad". |
| AI assistant | المساعد الذكي | Generic description of Sanad. |
| AI provider | مزوّد الذكاء الاصطناعي | OpenAI, Claude (Anthropic), Ollama, OpenRouter. Provider and product names stay in Latin script. |
| Chat | محادثة | pl. محادثات. One conversation with Sanad. |
| Model (AI) | النموذج | The generative AI model; keep the provider/model token (e.g. `openai/gpt-5`) in Latin script. |
| Approve (an action) | الموافقة / وافق | Confirming a destructive action Sanad asked to run. The approval buttons name the action itself: حذف / إبقاء (Delete / Keep) for a deletion, نشر / ليس الآن (Publish / Not now) for publishing a workflow. |
| Decline | رفض | |
| Instance administrator | مسؤول الخادم | pl. مسؤولو الخادم (مسؤولي الخادم after a preposition). Staff users: the only ones who can use Sanad and manage AI provider keys. |
| Ask Sanad | الاستعانة بسند | Button that hands a task to Sanad; verbal noun, like الاستعانة بمهارة. |
| Beta | بيتا | Badge on features still being introduced; matches the existing app-type badge. |
| Skill (Sanad) | مهارة | pl. مهارات. Expert guidance Sanad loads for one kind of work; "consulted a skill" = الاستعانة بمهارة. |
| Revision (Page view) | نسخة سابقة | pl. النسخ السابقة. A page's earlier document, kept on every rewrite; restore = استعادة نسخة سابقة. |
| Monthly allowance (Sanad) | الحصة الشهرية | The per-workspace budget of Sanad messages and tokens; "used up" = استُنفدت. |
| Public link | رابط عام | A share link anyone can open; sharing a form on one = مشاركة النموذج عبر رابط عام. Its approval reads نشر / ليس الآن like publishing a workflow. |

## Common actions (verbs)

| English | Arabic |
|---------|--------|
| Create | إنشاء |
| Add | إضافة |
| Edit | تعديل |
| Delete | حذف |
| Remove | إزالة |
| Rename | إعادة تسمية |
| Duplicate | تكرار |
| Save | حفظ |
| Cancel | إلغاء |
| Search | بحث |
| Filter | تصفية |
| Sort | ترتيب |
| Group by | تجميع حسب |
| Hide / Show | إخفاء / إظهار |
| Export | تصدير |
| Import | استيراد |
| Sign in / Log in | تسجيل الدخول |
| Sign up | إنشاء حساب |
| Log out | تسجيل الخروج |
| Share | مشاركة |
| Invite | دعوة |

## Conventions

- **Numbers & digits:** the UI defaults to **Western Arabic numerals (0–9)**, not
  Eastern (٠–٩), per the audit decision (Eastern digits are a later opt-in toggle —
  see docs/AUDIT.md §3.3). Keep numerals as ASCII in translation strings.
- **Latin brand/technical tokens** (URL, API, SKU, Jadawel-derived identifiers) stay
  Latin/LTR inside Arabic sentences; rely on `dir="auto"`/bidi, don't force-translate.
- **Placeholders / interpolation** (`{name}`, `{count}`, `@:action.save`) must be kept
  verbatim — translate only the surrounding words.
- **Tone:** address the user with neutral MSA; avoid dialect. Prefer verbal nouns
  (المصدر «إنشاء») over imperatives for button-like actions where Jadawel's English is a
  bare verb, matching Saudi enterprise software conventions.

## Status

First pass covers the high-visibility shell (common actions, sidebar, settings,
notifications, dashboard, grid chrome). Remaining namespaces fall back to English until
the full machine-translation + native-review pass lands (tracked Phase 1.1 follow-up).
