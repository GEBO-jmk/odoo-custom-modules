# Field Asset Portal

**Odoo 19 Enterprise · Version 19.0.1.0.0 · License LGPL-3**

A custom Odoo module for managing physical installations across multiple customer sites. It tracks locations, installed assets, individual equipment items, and the full service request lifecycle — with a customer-facing portal so contractors, site owners, and occupants can view their assets and submit service requests without needing backend access.

---

## 1. Module Overview

Field Asset Portal (`field_asset_portal`) is built for system integrators and service companies that install and maintain equipment at third-party premises. It answers the question: *who installed what, where, and who is responsible for it?*

Key capabilities:

- **Location registry** — physical premises with address, legal site owner, and occupant/owner contact
- **Asset registry** — installed systems (e.g. a heat pump, a fire alarm panel) linked to a location
- **Equipment registry** — individual components within an asset (e.g. the compressor unit, the control board), each with its own part codes, serial numbers, and warranty tracking
- **Service action workflow** — structured service requests from portal submission through approval, scheduling, execution, and completion
- **Customer portal** — portal users (contractors, site owners, service companies) see only the records they are entitled to, can browse asset and equipment details, view service history, and submit new service requests
- **Automated notifications** — email sent to the requestor when a service request is approved or declined

---

## 2. Actor Model

The module is designed around a chain of accountability from manufacturer to end user.

```
Manufacturer
    └── System Integrator (us — the Odoo tenant)
            └── Contractor
                    └── Site Owner (legal building owner)
                            └── Owner/Occupant (the person using the premises)
```

### Roles and Portal Access

| Role | Odoo Partner | Portal access granted when |
|---|---|---|
| **Manufacturer** | `res.partner` | Set as `manufacturer_id` on `fap.equipment`. Can see equipment records and equipment-level service history via portal. |
| **System Integrator** | The Odoo company itself | Full backend access. Manages all records. Handles service request approval, scheduling, and execution. |
| **Contractor** | `res.partner` | Set as `contractor_id` on `fap.asset`. Sees all assets and locations where they are the contractor. Can submit and track service requests. |
| **Service Company** | `res.partner` | Set as `service_company_id` on `fap.asset` or overridden per `fap.equipment`. Sees all assets and equipment they are responsible for. |
| **Site Owner** | `res.partner` | Set as `site_owner_id` on `fap.location` (legal building owner, may differ from occupant). Currently stored for reference; not yet a portal access criterion. |
| **Owner/Occupant** | `res.partner` | Set as `owner_id` (required) on `fap.location`. Sees all locations, assets, and equipment at their premises. Can submit service requests. |

Portal access uses Odoo's `child_of` domain operator against `user.commercial_partner_id`, so an employee of a contractor company automatically gets the same access as the company itself.

---

## 3. Data Model

### `fap.location` — Location

Represents a physical premises (a building, a site, a floor, a plant room).

| Field | Type | Notes |
|---|---|---|
| `name` | Char (required) | Location name, tracked |
| `ref` | Char | Internal reference |
| `owner_id` | Many2one `res.partner` (required) | The person living or working at the premises (Owner/Occupant), tracked |
| `site_owner_id` | Many2one `res.partner` | Legal owner of the building/property (may differ from occupant) |
| `street`, `street2`, `city`, `zip` | Char | Address fields |
| `country_id`, `state_id` | Many2one | Country and state |
| `notes` | Html | Rich text notes |
| `active` | Boolean | Supports archiving |
| `asset_ids` | One2many → `fap.asset` | Reverse relation, used by record rules |
| `asset_count` | Integer (computed) | Count of linked assets, shown as smart button |

Inherits: `mail.thread`, `mail.activity.mixin`

### `fap.asset` — Asset

Represents a complete installed system at a location (e.g. a ventilation unit, a fire alarm system).

| Field | Type | Notes |
|---|---|---|
| `name` | Char (required) | Asset name, tracked |
| `ref` | Char | Internal reference |
| `location_id` | Many2one `fap.location` (required) | Parent location, cascade delete, tracked |
| `contractor_id` | Many2one `res.partner` | Company that installed/maintains the asset |
| `service_company_id` | Many2one `res.partner` | Default service company for the asset (can be overridden per equipment) |
| `warranty_start` | Date | Start of our warranty to the contractor |
| `warranty_duration` | Integer | Duration in months (default 12) |
| `warranty_end` | Date (computed, stored) | `warranty_start + warranty_duration months` |
| `warranty_status` | Selection (computed, stored) | `active` / `expiring_soon` (< 1 month) / `expired` / `not_set` |
| `notes` | Html | Rich text notes |
| `active` | Boolean | Supports archiving |
| `equipment_ids` | One2many → `fap.equipment` | Linked equipment items |
| `equipment_count` | Integer (computed) | Smart button count |
| `service_action_count` | Integer (computed) | Smart button count |

Inherits: `mail.thread`, `mail.activity.mixin`, `portal.mixin` (provides `access_token`)

### `fap.equipment` — Equipment

Represents an individual component within an asset (e.g. a compressor, a sensor, a control board). Tracks two independent warranty chains: the manufacturer's warranty and our own warranty to the contractor.

| Field | Type | Notes |
|---|---|---|
| `name` | Char (required) | Equipment name, tracked |
| `asset_id` | Many2one `fap.asset` (required) | Parent asset, cascade delete, tracked |
| `location_id` | Many2one `fap.location` (related, stored) | Denormalised from `asset_id.location_id` |
| `manufacturer_id` | Many2one `res.partner` | Manufacturer |
| `service_company_id` | Many2one `res.partner` | Overrides asset-level service company for this specific item |
| `manufacturer_part_code` | Char | Manufacturer's part number |
| `manufacturer_serial` | Char | Manufacturer's serial number |
| `your_part_code` | Char | Our internal part code |
| `your_serial` | Char | Our internal serial number |
| `manufacturer_warranty_start/duration/end/status` | Date/Integer/Date/Selection | Manufacturer warranty (computed, stored) |
| `our_warranty_start/duration/end/status` | Date/Integer/Date/Selection | Our warranty to contractor (computed, stored) |
| `notes` | Html | Rich text notes |
| `active` | Boolean | Supports archiving |
| `service_action_count` | Integer (computed) | Smart button count |

Warranty status values (same for both warranty types): `active` / `expiring_soon` (< 1 month) / `expired` / `not_set`

Inherits: `mail.thread`, `mail.activity.mixin`, `portal.mixin` (provides `access_token`)

### `fap.service.action` — Service Action

A service request or work order, from initial portal submission through to completion.

| Field | Type | Notes |
|---|---|---|
| `name` | Char (required) | Summary / title, tracked |
| `ref` | Char (readonly) | Auto-generated sequence `SA-00001` |
| `asset_id` | Many2one `fap.asset` (required) | Asset being serviced, tracked |
| `equipment_id` | Many2one `fap.equipment` | Optional specific equipment item (domain filtered to `asset_id`) |
| `location_id` | Many2one `fap.location` (related, stored) | Denormalised from `asset_id.location_id` |
| `action_type` | Selection (required) | `installation` / `preventive` / `corrective` / `predictive` / `calibration` / `inspection` / `parts_replacement` |
| `state` | Selection (required) | See workflow below |
| `priority` | Selection | `0` Normal / `1` Urgent / `2` Critical |
| `requested_by_id` | Many2one `res.partner` | Set automatically from portal user on submit |
| `assigned_to_id` | Many2one `res.users` | Internal staff member responsible, tracked |
| `date_requested` | Datetime | Defaults to now |
| `date_scheduled` | Datetime | Planned service date |
| `date_completed` | Datetime | Set automatically when marked Done |
| `description` | Html | Detailed description of the issue |
| `resolution` | Html | Resolution notes (filled after work is done) |

Inherits: `mail.thread`, `mail.activity.mixin`

Sequence: `ir.sequence` code `fap.service.action`, prefix `SA-`, padding 5 → `SA-00001`

---

## 4. Warranty Chain

The module tracks a three-layer warranty structure:

```
[Layer 1] Manufacturer → Us (System Integrator)
    Tracked on fap.equipment:
    - manufacturer_warranty_start
    - manufacturer_warranty_duration / manufacturer_warranty_end
    - manufacturer_warranty_status

[Layer 2] Us (System Integrator) → Contractor
    Tracked on fap.equipment (and summarised on fap.asset):
    - our_warranty_start
    - our_warranty_duration / our_warranty_end
    - our_warranty_status

[Layer 3] Contractor → Site Owner / Occupant
    Not yet tracked in the module (Phase 3 roadmap item).
    The contractor manages their own warranty obligation to the end user.
```

Warranty end dates are computed and stored (`@api.depends`, `store=True`) using `relativedelta` for accurate month arithmetic. Status is recomputed whenever the end date changes:

- `active` — end date is in the future and more than 1 month away
- `expiring_soon` — end date is within the next calendar month
- `expired` — end date is in the past
- `not_set` — no start date or duration set

The 1-month expiring-soon threshold applies to both warranty types on equipment and to the asset-level warranty.

---

## 5. Portal Access

### How Record Rules Work

Four `ir.rule` records restrict portal users (`base.group_portal`) using `domain_force` with `child_of user.commercial_partner_id.id`. This means a portal user sees a record if their company (or any of its subsidiaries) appears in any of the following roles:

| Model | Access granted if user's partner is... |
|---|---|
| `fap.location` | `owner_id` OR `asset_ids.contractor_id` OR `asset_ids.service_company_id` OR `asset_ids.equipment_ids.service_company_id` |
| `fap.asset` | `location_id.owner_id` OR `contractor_id` OR `service_company_id` OR `equipment_ids.service_company_id` |
| `fap.equipment` | `asset_id.location_id.owner_id` OR `asset_id.contractor_id` OR `asset_id.service_company_id` OR `service_company_id` |
| `fap.service.action` | `asset_id.location_id.owner_id` OR `asset_id.contractor_id` OR `asset_id.service_company_id` OR `equipment_id.service_company_id` |

The `One2many` fields `asset_ids` on `fap.location` and `equipment_ids` on `fap.asset` exist specifically to enable record rule domain traversal (Odoo requires the reverse relation to be present for `child_of` traversal through a `One2many`).

### ACL (ir.model.access.csv)

| Group | Locations | Assets | Equipment | Service Actions |
|---|---|---|---|---|
| `base.group_user` (internal) | CRUD | CRUD | CRUD | CRUD |
| `base.group_portal` | Read only | Read only | Read only | Read only |

Portal users can **create** service actions via the `sudo()` call in the controller submit route — this bypasses the read-only ACL restriction for that one operation. All other write operations (approve, decline, etc.) are internal only.

### Portal Controller Pattern

All portal routes use the pattern:
```python
# 1. Search without sudo — record rules apply, filters to accessible records
asset_ids = request.env['fap.asset'].search([('id', '=', asset_id)]).ids
# 2. Browse with sudo — bypass ACL to read all related fields
asset = request.env['fap.asset'].sudo().browse(asset_ids[0])
```

This ensures:
- The portal user can only access records they are entitled to (record rules enforced on search)
- Related fields (partner names, nested relations) are fully readable (sudo on browse)

### What Portal Users Can Do

- View the "Your Assets" tile on the portal home page with asset count
- Browse `/my/assets` — list of all their accessible assets
- View `/my/assets/<id>` — asset detail with warranty info, equipment list, service history, and chatter
- View `/my/equipment/<id>` — equipment detail with both warranty chains, service history, and chatter
- Submit service requests from three entry points:
  - Asset detail page ("Request Service" button)
  - Equipment row ("Request Service" per equipment)
  - Asset list ("Request Service" button at top when all assets share one location)
- Service request form supports: location (read-only), asset selection, summary, type, equipment selection, and description

Portal users **cannot**: approve/decline/confirm/complete service requests, create or edit locations/assets/equipment, or see records belonging to other companies.

---

## 6. Service Action Workflow

### State Machine

```
                    ┌─────────┐
    [Portal submit] │ pending │ ◄── action_set_pending (Send for Review)
                    └────┬────┘
                         │ action_approve (Approve) ──► sends approval email
                         ▼
                    ┌─────────┐
          default ► │  draft  │ (displayed as "Approved")
                    └────┬────┘
                         │ action_confirm (Confirm)
                         ▼
                    ┌───────────┐
                    │ confirmed │
                    └─────┬─────┘
                          │ action_start (Start)
                          ▼
                    ┌─────────────┐
                    │ in_progress │
                    └──────┬──────┘
                           │ action_done (Mark Done) ──► sets date_completed
                           ▼
                        ┌──────┐
                        │ done │
                        └──────┘

From pending:   action_decline (Decline) ──► sends decline email ──► declined
From anywhere:  action_cancel ──► cancelled
From cancelled: action_reset ──► draft
```

### State Descriptions

| State | Display Name | Meaning |
|---|---|---|
| `pending` | Pending | Submitted via portal, awaiting internal review |
| `draft` | Approved | Accepted by internal team, not yet formally scheduled |
| `confirmed` | Confirmed | Scheduled and committed |
| `in_progress` | In Progress | Work has started on site |
| `done` | Done | Work completed; `date_completed` recorded |
| `declined` | Declined | Request rejected; decline email sent |
| `cancelled` | Cancelled | Withdrawn or voided |

### Email Notifications

Two `mail.template` records are defined:

- **Approved** (`mail_template_service_action_approved`): sent when `action_approve()` is called, to `requested_by_id.email`
- **Declined** (`mail_template_service_action_declined`): sent when `action_decline()` is called, to `requested_by_id.email`

Both templates are sent with `force_send=True` and only fire if the requestor has an email address. The templates use numeric XML entities (`&#8212;`) instead of named HTML entities, which are not valid in Odoo data XML.

### Who Triggers Each Transition

| Transition | Triggered by |
|---|---|
| `pending` (submit) | Portal user via `/my/service/submit` (sudo create) |
| `pending` (Send for Review) | Internal user — moves an approved request back to pending for re-review |
| `draft` (Approve) | Internal user |
| `declined` (Decline) | Internal user |
| `confirmed` (Confirm) | Internal user |
| `in_progress` (Start) | Internal user or assigned technician |
| `done` (Mark Done) | Internal user or assigned technician |
| `cancelled` (Cancel) | Internal user |
| `draft` (Reset to Draft) | Internal user |

---

## 7. Module Structure

```
field_asset_portal/
├── __init__.py                        # Python package root
├── __manifest__.py                    # Module metadata, dependencies, data load order
│
├── models/
│   ├── __init__.py                    # Imports all model modules
│   ├── fap_location.py                # fap.location model — physical premises
│   ├── fap_asset.py                   # fap.asset model — installed systems
│   ├── fap_equipment.py               # fap.equipment model — individual components
│   └── fap_service_action.py          # fap.service.action model — service requests
│
├── views/
│   ├── fap_location_views.xml         # Location form/list/search + menu root
│   ├── fap_asset_views.xml            # Asset form/list/search + menu item
│   ├── fap_equipment_views.xml        # Equipment form/list/search + menu item
│   ├── fap_service_action_views.xml   # Service action form/list/search + menu item
│   ├── fap_pending_inbox_views.xml    # Filtered list of pending service requests + menu
│   └── portal_templates.xml          # All portal QWeb templates
│
├── controllers/
│   ├── __init__.py                    # Imports portal controller
│   └── portal.py                      # CustomerPortal extension — all portal routes
│
├── security/
│   ├── ir.model.access.csv            # ACL — internal users CRUD, portal read-only
│   └── record_rules.xml               # Portal record rules — child_of domain per model
│
├── data/
│   ├── sequences.xml                  # SA-00001 sequence for service action refs
│   └── mail_templates.xml             # Approved and declined notification emails
│
├── i18n/
│   ├── field_asset_portal.pot         # Translation source file (generated)
│   ├── fi.po                          # Finnish translations
│   └── sv.po                          # Swedish translations
│
└── static/
    └── description/
        ├── icon.png                   # 128×128 module icon
        └── icon.svg                   # SVG icon used in portal home tile
```

### Data Load Order (from `__manifest__.py`)

Data files must be loaded in dependency order:
1. `data/sequences.xml` — sequence must exist before service actions can be created
2. `data/mail_templates.xml` — templates reference `model_fap_service_action`
3. Views (location → asset → equipment → service action → pending inbox → portal)
4. Security last — ACL and record rules reference model xmlids that must already exist

---

## 8. Development Setup

### Local Environment

The development environment uses Docker via OrbStack on macOS. The Odoo 19 container is named `odoo19-dev-odoo-1`.

Common commands:

```bash
# Restart Odoo to pick up Python changes
docker restart odoo19-dev-odoo-1

# Update the module (picks up XML/data changes without full restart)
docker exec odoo19-dev-odoo-1 odoo -d <dbname> -u field_asset_portal --stop-after-init

# Tail logs
docker logs -f odoo19-dev-odoo-1

# Check if a template/file exists in the container
docker exec odoo19-dev-odoo-1 grep -r "template id=" \
  /usr/lib/python3/dist-packages/odoo/addons/portal/views/

# Open a shell in the container
docker exec -it odoo19-dev-odoo-1 bash
```

The module source is mounted into the container from the host at:
```
/Users/johankarlstedt/odoo19-dev/addons/field_asset_portal/
```

### Pushing to GitHub / Odoo.sh

```bash
cd /Users/johankarlstedt/odoo19-dev/addons
git add field_asset_portal/
git commit -m "feat: describe what changed"
git push origin main
```

Odoo.sh picks up the push automatically and redeploys the staging branch.

### Development Workflow with Claude

This module is developed iteratively using Claude Code (CLI) as the primary coding assistant. The typical session flow:

1. Start a Claude Code session in `/Users/johankarlstedt/odoo19-dev/addons`
2. Describe the feature or fix needed
3. Claude reads the relevant files, proposes changes, and applies them directly
4. Test in the running Odoo container; report errors back to Claude
5. Commit when the feature works

The session context compresses automatically as it grows. The `README.md` and the conversation summary stored in `~/.claude/projects/` serve as the briefing document for new sessions. When starting a new session after context compression, paste the README into the conversation or ask Claude to read it.

---

## 9. Roadmap

### Phase 3 — Sales Integration and Commissioning

- Link assets and equipment to Odoo Sale Orders and/or Bills of Materials
- Commissioning workflow: record the handover from us to the contractor, with sign-off and documentation
- Track which sale order line corresponds to which installed asset or equipment item
- Contractor warranty start date auto-set from commissioning/delivery date

### Phase 4 — Documents and Media

- Attach installation manuals, datasheets, and certificates to equipment records
- Photo gallery per asset/equipment (before/after service photos)
- Document portal: portal users can download their relevant documents
- Integrate with Odoo Documents module if available

### Phase 5 — IoT and Monitoring

- Link equipment to IoT sensor readings (temperature, pressure, runtime hours)
- Trigger automatic service requests based on threshold breaches or maintenance intervals
- Dashboard view of asset health across all locations

### Smaller Near-Term Items

- **Service request categories config**: make `action_type` selection configurable via settings rather than hardcoded in the model
- **Portal list filtering and sorting**: add search/filter/sort controls to the `/my/assets` portal page (warranty status filter, location filter, sort by name/warranty date)
- **Sale order linkage**: `sale_order_id` Many2one on `fap.asset` and `fap.service.action` for traceability back to the original sale
- **Contractor warranty to end user**: Layer 3 warranty tracking (the contractor's warranty obligation to the site owner/occupant)
- **Scheduled maintenance**: recurring service actions based on time intervals or meter readings
- **Service action PDF report**: printable work order / completion certificate

---

## 10. Technical Notes (Odoo 19 Gotchas)

These were discovered during development and will save time in future sessions.

### `active_id` vs `id` in button context attributes

In form view button `context` attributes, use `id` (the record's own ID), not `active_id`. In Odoo 19, `active_id` is not available as an evaluation variable in view attribute expressions:

```xml
<!-- Wrong -->
context="{'default_asset_id': active_id}"

<!-- Correct -->
context="{'default_asset_id': id}"
```

### Smart button type must be `type="object"`

Smart buttons that open related record lists must use `type="object"` with a Python method that returns an `ir.actions.act_window` dict. Using `type="action"` with an xmlid causes a view load error:

```xml
<!-- Wrong — fails at view load time -->
<button type="action" name="%(field_asset_portal.fap_asset_action)d" .../>

<!-- Correct -->
<button type="object" name="action_open_assets" .../>
```

### `portal.portal_chatter` does not exist in Odoo 19 Community

The portal chatter/messaging widget is `portal.message_thread`, not `portal.portal_chatter`. The correct variables are `object`, `token`, `pid`, and `hash`:

```xml
<!-- Wrong — "Template not found" error -->
<t t-call="portal.portal_chatter">
    <t t-set="display_rating" t-value="False"/>
</t>

<!-- Correct -->
<t t-call="portal.message_thread">
    <t t-set="object" t-value="asset"/>
    <t t-set="token" t-value="asset.access_token"/>
    <t t-set="pid" t-value="request.env.user.partner_id.id"/>
    <t t-set="hash" t-value="asset.access_token"/>
</t>
```

### Search view group syntax

In Odoo 19, `<group>` elements inside `<search>` views are invalid. Use `<separator/>` between filters instead:

```xml
<!-- Wrong -->
<search>
    <group expand="0" string="Group By">
        <filter name="group_by_owner" .../>
    </group>
</search>

<!-- Correct -->
<search>
    <separator/>
    <filter name="group_by_owner" .../>
</search>
```

### Named HTML entities are invalid in data XML

Odoo data XML files do not support named HTML entities like `&mdash;`. Use numeric equivalents:

```xml
<!-- Wrong — XML parse error -->
&mdash;

<!-- Correct -->
&#8212;
```

This applies to view XML files, mail template `body_html` fields, and any other XML data file.

### Badge decoration values

The `decoration-secondary` attribute on `widget="badge"` fields does not exist in Odoo 19. Use `decoration-muted` for neutral/grey states:

```xml
<!-- Wrong -->
decoration-secondary="state == 'cancelled'"

<!-- Correct -->
decoration-muted="state == 'cancelled'"
```

### Portal breadcrumb architecture

`portal_layout` renders the breadcrumb automatically via `portal.portal_breadcrumbs` in a container div above the content area. Do **not** add a manual `<nav>/<ol>` inside the template content — this creates a duplicate breadcrumb. Instead, extend `portal.portal_breadcrumbs` with `inherit_id` and branch on `page_name`:

```xml
<template id="portal_breadcrumbs_field_asset" inherit_id="portal.portal_breadcrumbs">
    <xpath expr="//ol" position="inside">
        <t t-if="page_name == 'asset_detail' and asset">
            <li class="breadcrumb-item ms-1"><a href="/my/assets">My Assets</a></li>
            <li class="breadcrumb-item ms-1 active"><t t-out="asset.name"/></li>
        </t>
    </xpath>
</template>
```

Pass distinct `page_name` values from each controller route (`'asset_detail'`, `'equipment_detail'`, `'service_request'`) so the extension can branch correctly. The `page_name='assets'` value (used by the list page with `breadcrumbs_searchbar=True`) is also handled by the same extension.

### `portal.mixin` and `_portal_ensure_token()`

To use `portal.message_thread` on a model, the model must inherit `portal.mixin`. Call `_portal_ensure_token()` in the controller **before** rendering the template to guarantee the `access_token` field is populated:

```python
asset = request.env['fap.asset'].sudo().browse(asset_ids[0])
asset.sudo()._portal_ensure_token()
```

### `trans_export` API in Odoo 19

The Odoo 19 translation export API changed. `Environment.manage()` was removed and `trans_export` takes an `env` object (not a cursor) as its last argument:

```python
from odoo.tools.translate import trans_export
from odoo.registry import Registry

registry = Registry('your_db_name')
with registry.cursor() as cr:
    env = odoo.api.Environment(cr, odoo.SUPERUSER_ID, {})
    with open('field_asset_portal.pot', 'wb') as f:
        trans_export('en_US', ['field_asset_portal'], f, 'po', env)
```

The `--i18n-export` CLI flag was removed in Odoo 19.

### Portal sudo pattern

Always use the two-step pattern in portal controllers. Do not search with sudo (bypasses record rules) and do not browse without sudo (related fields may be inaccessible):

```python
# Step 1: search without sudo — record rules apply
asset_ids = request.env['fap.asset'].search([('id', '=', asset_id)]).ids

# Step 2: if no results, the user has no access — redirect
if not asset_ids:
    return request.redirect('/my/assets')

# Step 3: browse with sudo — all related fields readable
asset = request.env['fap.asset'].sudo().browse(asset_ids[0])
```

### `One2many` fields required for record rule traversal

For record rules that traverse a `One2many` relationship (e.g. `asset_ids.contractor_id` in the location rule), the `One2many` field must be explicitly defined on the model even if it is not displayed in any view. Without it, Odoo cannot resolve the domain:

```python
# Required on fap.location for the record rule domain to work:
asset_ids = fields.One2many('fap.asset', 'location_id', string='Asset List')
```

### Portal home tile variables

The `portal.portal_docs_entry` template (used for the "Your Assets" home tile) uses `count` and `placeholder_count`, not `document_count`. The `placeholder_count` value must match the counter key in `_prepare_home_portal_values`:

```xml
<t t-set="placeholder_count" t-value="'asset_count'"/>
<t t-set="count" t-value="asset_count"/>
```

```python
def _prepare_home_portal_values(self, counters):
    if 'asset_count' in counters:
        values['asset_count'] = ...
```

The icon variable is `icon` (not `icon_src`) and takes a path relative to the web root.
