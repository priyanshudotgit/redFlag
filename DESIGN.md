# redFlag Design System (DESIGN.md)

**Project:** redFlag — Public Abuse & Civic Grievance Reporting System  
**Art Direction:** The Printed Annual (`editorial-report`) + Civic Accountability Reference  
**Design Inspirations:** Taste Skill Distillation & Gov.uk Form/Accessibility Principles  

---

## 1. Brand Principles

1. **Sober Civic Authority, Not Institutional Deception:**
   - redFlag does not mimic official state crests or invent fake accreditation badges.
   - Trust is earned through crisp editorial typography, absolute transparency, strict data privacy, and predictable workflows.
2. **Deliberate Accent Usage:**
   - The brand name `redFlag` does not justify drowning screens in harsh crimson.
   - Crimson / Scarlet (`#DC2626` / `#B91C1C`) is reserved exclusively for vital actions (Flag an Incident, critical warnings, urgent statuses).
   - Chrome remains neutral, calm, and readable.
3. **Clarity Over Novelty:**
   - No floating cards with arbitrary drop shadows, no glassmorphism, no rainbow gradients.
   - High legibility, semantic structure, unambiguous labels, and generous touch targets.
4. **Accessible by Default:**
   - WCAG 2.1 AA compliant contrast (minimum 4.5:1 for body text, 3:1 for large display headers).
   - High-visibility focus indicators (2px solid ring with 2px offset).
   - Full keyboard accessibility across forms, navigation, and review controls.

---

## 2. Color Tokens

### 2.1 Core Palette
```css
:root {
  /* Surfaces & Grounds */
  --color-ground: #F8F9FA;         /* Warm bone / soft paper ground */
  --color-surface: #FFFFFF;        /* Pure white for form sheets & cards */
  --color-surface-subtle: #F1F5F9; /* Slate 100 for sidebars and headers */
  --color-surface-sunken: #E2E8F0; /* Slate 200 for rules and dividers */

  /* Inks & Text */
  --color-ink-primary: #0F172A;   /* Slate 900 for headings and primary copy */
  --color-ink-secondary: #334155; /* Slate 700 for descriptions and subheads */
  --color-ink-muted: #64748B;     /* Slate 500 for captions, timestamps, meta */
  --color-ink-inverted: #FFFFFF;  /* Inverted text on dark backgrounds */

  /* Brand & Critical Flags */
  --color-flag-red: #DC2626;      /* Red 600 - Primary brand and emergency accent */
  --color-flag-red-hover: #B91C1C;/* Red 700 - Hover state */
  --color-flag-red-subtle: #FEF2F2;/* Red 50 - Alert backgrounds */
  --color-flag-red-border: #FCA5A5;/* Red 300 - Alert borders */

  /* Status Tokens */
  --status-submitted-text: #475569;  /* Slate 600 */
  --status-submitted-bg: #F1F5F9;    /* Slate 100 */
  --status-submitted-border: #CBD5E1;/* Slate 300 */

  --status-review-text: #92400E;     /* Amber 800 */
  --status-review-bg: #FEF3C7;       /* Amber 100 */
  --status-review-border: #FCD34D;   /* Amber 300 */

  --status-investigating-text: #075985; /* Sky 800 */
  --status-investigating-bg: #E0F2FE;   /* Sky 100 */
  --status-investigating-border: #7DD3FC;/* Sky 300 */

  --status-resolved-text: #166534;   /* Emerald 800 */
  --status-resolved-bg: #DCFCE7;     /* Emerald 100 */
  --status-resolved-border: #86EFAC; /* Emerald 300 */

  --status-closed-text: #991B1B;     /* Red 800 */
  --status-closed-bg: #FEE2E2;       /* Red 100 */
  --status-closed-border: #FCA5A5;   /* Red 300 */

  /* Focus & Focus-Visible */
  --color-focus: #0F172A;            /* High-contrast focus outline */
  --color-focus-ring: #94A3B8;       /* Subtle outer halo */
}
```

---

## 3. Typography

### 3.1 Type Families
- **Display & Headings:** `Literata`, Georgia, serif (Editorial gravitas, sharp optical sizing, readable in sentence case).
- **Body & Forms:** Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif (Precision legibility, crisp tabular numerals).
- **Data & Codes:** ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace (Used strictly for incident tracking references, timestamps, and coordinates).

### 3.2 Scale & Leading
```css
/* Fluid Typography Scale */
--step-caption: clamp(0.75rem, 0.73rem + 0.1vw, 0.8125rem);  /* 12-13px */
--step-small:   clamp(0.8125rem, 0.79rem + 0.15vw, 0.875rem); /* 13-14px */
--step-base:    clamp(1rem, 0.98rem + 0.1vw, 1.0625rem);       /* 16-17px */
--step-lead:    clamp(1.125rem, 1.05rem + 0.35vw, 1.25rem);   /* 18-20px */
--step-title:   clamp(1.5rem, 1.35rem + 0.75vw, 1.875rem);    /* 24-30px */
--step-display: clamp(2rem, 1.6rem + 2vw, 3.25rem);           /* 32-52px */
```
- Line heights: Headings `1.15`, Lead paragraphs `1.4`, Body paragraphs `1.6`, Form inputs `1.5`.
- Rules: Never set headlines over 3 lines at any viewport; avoid letter-spacing on serifs; track uppercase mono tracking at `0.05em`.

---

## 4. Spacing, Layout & Breakpoints

### 4.1 Spacing Scale
- 4px (`space-1`), 8px (`space-2`), 12px (`space-3`), 16px (`space-4`), 24px (`space-6`), 32px (`space-8`), 48px (`space-12`), 64px (`space-16`).

### 4.2 Containers & Breakpoints
- Breakpoints: `sm: 640px`, `md: 768px`, `lg: 1024px`, `xl: 1280px`.
- Form & Article Reading Max Width: `max-w-3xl` (768px) for optimal line measure (55–75 characters per line).
- Dashboard & Queue Max Width: `max-w-7xl` (1280px) with comfortable padding (`px-4 sm:px-6 lg:px-8`).

---

## 5. Components & Interaction Guidelines

### 5.1 Buttons
- **Primary Flag Action:**
  - Red background (`bg-red-600 hover:bg-red-700 active:bg-red-800`), white text, medium weight, `px-5 py-2.5`, rounded `rounded-md`, transition duration 150ms.
- **Secondary Action:**
  - Solid dark slate (`bg-slate-900 hover:bg-slate-800 text-white`), clean contrast for administrative/staff actions.
- **Outline / Quiet Action:**
  - White surface, 1px border (`border-slate-300 text-slate-700 hover:bg-slate-50`).
- **Destructive Action:**
  - Bordered or filled red button with explicit confirmation step.

### 5.2 Forms & Validation
- **Labels:** Explicit `<label for="id">` for every single control. Upper small label or regular title with clear `(Required)` indicator.
- **Inputs & Textareas:**
  - Crisp 1px border (`border-slate-300 focus:border-slate-900 focus:ring-1 focus:ring-slate-900`).
  - Background: White (`bg-white`).
  - Placeholder: Light muted (`placeholder-slate-400`).
- **Error States:**
  - Input border changes to `border-red-600 focus:border-red-600 focus:ring-red-600`.
  - Accessible error message directly below input with `aria-live="polite"` and `id="error-<fieldname>"` linked via `aria-describedby`.
  - Gov.uk style Error Summary box rendered at the top of the form when server validation fails, anchoring to invalid fields.

### 5.3 Status Badges
- Pill badges rendered as `inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium border`.
- Each status has an associated icon (SVG dot, check, eye, or alert) to avoid relying solely on color.

### 5.4 Data Tables (Staff Review Queue)
- No zebra striping. Clean horizontal dividing lines (`divide-y divide-slate-200`).
- Clear column headers (`text-xs font-semibold uppercase tracking-wider text-slate-500`).
- Responsive scroll container (`overflow-x-auto`) with mobile card fallback for small viewports.

### 5.5 Alerts & Messages
- Using Django's built-in messages framework (`info`, `success`, `warning`, `error`).
- Rendered in a fixed or prominent toast banner below navigation with a distinct icon and dismiss button.

---

## 6. Motion & Accessibility

- **Reduced Motion:** Wrap transitions in `@media (prefers-reduced-motion: reduce) { transition: none !important; animation: none !important; }`.
- **Keyboard Navigation:** Every interactive element has an active `:focus-visible` state. Skip link (`#main-content`) provided on all pages.
- **Screen Reader Announcements:** Dynamic state changes, errors, and feedback carry proper ARIA attributes (`role="status"`, `role="alert"`, `aria-live="polite"`).

