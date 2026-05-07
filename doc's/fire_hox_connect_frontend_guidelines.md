# FireHox Connect — Frontend Guidelines (Design System + UI Rules)

## 1. Design Philosophy

Core Principle:
"Focus, clarity, and zero distraction during execution"

You are NOT building a flashy AI product.
You are building a **high-focus workspace**.

Design Goals:
- Minimal cognitive load
- Instant readability
- Fast interaction
- Clear hierarchy

---

## 2. Layout Structure (Meeting Screen)

### Primary Layout

| Left Sidebar | Main Video Area | Right AI Sidebar |

- Left Sidebar: collapsible tools
- Center: video (primary focus)
- Right Sidebar: AI drafts (USP)

---

### 2.1 Left Sidebar

Width: 64px (collapsed), 220px (expanded)

Elements:
- Security icon
- Participants
- Chat
- Share
- Record
- Settings

Behavior:
- Toggle collapse/expand
- Icons only in collapsed state
- Tooltip on hover

Style:
- Background: #0B0F14
- Border-right: 1px solid #1C222B

---

### 2.2 Main Video Area

Layout:
- Grid (2 participants default)
- Responsive grid for more users

Video Card:
- Border-radius: 16px
- Background: #11161C
- Shadow: subtle (0 4px 20px rgba(0,0,0,0.4))

Spacing:
- Gap: 16px
- Padding: 24px

---

### 2.3 Bottom Control Bar

Position:
- Fixed bottom center

Style:
- Background: rgba(20, 25, 32, 0.85)
- Backdrop blur
- Border-radius: 20px

Buttons:
- Mic
- Camera
- Reactions
- End Meeting

Button Style:
- Size: 44px
- Icon centered
- Hover: subtle scale (1.05)

End Button:
- Background: #FF4D4F
- Text: white

---

### 2.4 Right AI Sidebar (CORE USP)

Width:
- Default: 360px
- Adjustable: 300px – 480px

Background:
- #0F141A

Border:
- Left border: 1px solid #1C222B

Sections:
1. Header ("AI Panel")
2. Draft Cards List
3. Caption / Info Section

Behavior:
- Resizable
- Collapsible

---

## 3. Draft Card Design (MOST IMPORTANT)

Card Style:
- Background: #151B23
- Border-radius: 16px
- Padding: 16px
- Margin-bottom: 12px

States:

### Pending
- Border: 1px solid #2A3340

### Approved
- Border: 1px solid #2ECC71
- Glow: subtle green

### Low Confidence (future)
- Border: 1px dashed #F39C12

---

### Card Content

Typography:
- Title: 16px, font-weight 600
- Meta: 13px, color #9AA4B2

Fields:
- Task title
- Assignee
- Deadline

---

### Actions

Buttons:
- Edit
- Approve

Style:
- Edit: outline button
- Approve: primary accent

Approve Button:
- Background: #2ECC71
- Hover: #27AE60

---

## 4. Typography System

Font Family:
- Inter (primary)

Weights:
- 400 (regular)
- 500 (medium)
- 600 (semi-bold)

Scale:
- 12px (meta)
- 14px (body)
- 16px (title)
- 20px (section)

---

## 5. Color System

### Backgrounds
- Primary: #0B0F14
- Secondary: #11161C
- Tertiary: #151B23

### Borders
- #1C222B

### Text
- Primary: #E6EDF3
- Secondary: #9AA4B2

### Accent
- Green: #2ECC71
- Red: #FF4D4F
- Blue (optional): #3B82F6

---

## 6. Spacing System

Base unit: 4px

Spacing scale:
- 4px
- 8px
- 12px
- 16px
- 24px
- 32px

---

## 7. Interaction Rules

- No intrusive popups
- No modal spam
- Everything in sidebar

---

## 8. Animation Guidelines

- Duration: 150–250ms
- Easing: ease-out

Animations:
- Draft appear → slide-in
- Hover → slight scale
- Approve → color transition

---

## 9. Responsiveness

Breakpoints:
- Desktop: full layout
- Tablet: collapse left sidebar
- Mobile: not supported in MVP

---

## 10. Accessibility

- Contrast ratio maintained
- Click targets ≥ 40px
- Keyboard navigation (basic)

---

## 11. UX Rules (CRITICAL)

- Video is context
- Sidebar is product
- Zero clutter

---

## 12. Empty States

When no drafts:
Show message:
"No actions detected yet"

---

## 13. Loading States

- Show subtle loader in sidebar
- Text: "Listening..."

---

## 14. Error States

- Minimal inline errors
- No blocking UI

---

## 15. Final Definition

The UI must feel:
- Clean
- Fast
- Focused

If it feels like a dashboard → you failed.
If it feels like a workspace → you succeeded.

