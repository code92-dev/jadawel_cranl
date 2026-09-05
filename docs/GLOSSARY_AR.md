# Arabic Terminology Glossary — Jadawel (جداول)

Single source of truth for how Jadawel/Jadawel product terms are translated into
Arabic. **Every `ar.json` translation must use these exact terms** so the UI reads
consistently. When you introduce a new recurring term, add it here first.

Arabic is the **primary** locale; keep translations natural for a Saudi business/
government audience (Modern Standard Arabic, no transliteration where a real Arabic
term exists).

## Core product nouns

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
| Trash | سلة المهملات | |
| Snapshot | لقطة | pl. لقطات |
| Member | عضو | pl. الأعضاء |
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

## MCP data protection

| English | Arabic | Notes |
|---------|--------|-------|
| Protected field | حقل محمي | A field whose non-empty values are replaced with mask tokens at its MCP endpoint boundary. Do not use حقل مشفّر. |
| Endpoint protection policy | سياسة حماية الحقول | The protected fields selected for one MCP endpoint. |
| Mask token | رمز إخفاء | An opaque reference returned through MCP instead of a protected value. |
| Protected derivative | مشتق محمي | A value that would reproduce or expose information from a protected field. |

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
