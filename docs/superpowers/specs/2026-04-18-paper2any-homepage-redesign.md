# Paper2Any Homepage Redesign

Date: 2026-04-18
Project: `frontend-workflow`
Scope: redesign the Paper2Any homepage experience only

## 1. Summary

The current homepage behaves primarily as a dark visual catalog of tools. It exposes many workflows at once, but it does not explain the product clearly enough for a first-time visitor. The redesign shifts the homepage into a platform narrative:

1. Explain what Paper2Any is.
2. Show how the platform works.
3. Prove what it can produce.
4. Then expose the full workflow library.

The selected direction is:

- Platform narrative homepage
- Workflow map immediately after the hero
- Research editorial visual language

This gives the homepage two jobs, in this order:

- Help new visitors understand Paper2Any as an AI research expression platform.
- Support external presentation, partnership, and product-facing communication with a more credible brand surface.

## 2. Goals

- Make the first screen communicate product value in under a few seconds.
- Reposition the homepage from "tool list" to "platform homepage".
- Preserve discoverability of the existing workflows without letting them dominate the first impression.
- Support both academic and enterprise audiences, with the tone weighted toward academic research.
- Improve brand credibility, information hierarchy, and mobile readability.

## 3. Non-goals

- Redesigning the internal workflow pages in this pass.
- Changing backend routing or workflow behavior.
- Creating a full case-study CMS or dedicated marketing site.
- Rebranding the product identity, logo, or product name.

## 4. Target Audience

Primary audience:

- Students, researchers, labs, and academic teams who need to turn papers and research materials into presentation assets.

Secondary audience:

- Enterprise R&D, solution, or product teams evaluating the platform for technical communication and project presentation.

The homepage voice should remain research-oriented, but visually credible enough for external product demonstration.

## 5. Core Positioning

Primary positioning statement:

> Paper2Any is an AI research expression platform.

Core homepage promise:

> Turn research content into assets that can be presented, explained, and shared.

Supporting value themes that should repeat across sections:

- Editable
- Reusable
- Presentable
- Explainable
- Shareable

## 6. Information Architecture

Homepage section order:

1. Hero
2. Workflow Map
3. Result Showcase
4. Scenario Section
5. Full Feature Library

Why this order:

- The hero defines the platform.
- The workflow map explains the end-to-end path.
- The result showcase provides proof.
- The scenario section translates capabilities into user needs.
- The full library serves as the deep navigation surface after the user understands the product.

## 7. Section Design

### 7.1 Hero

Purpose:

- Establish the product as a unified platform, not a collection of unrelated tools.

Content:

- Kicker: `AI Research Expression Platform`
- Headline: a single platform-level message
- One short description paragraph
- Two CTAs:
  - Primary: browse workflow map
  - Secondary: view result examples
- Three compact proof chips:
  - Inputs
  - Platform engine
  - Outputs

Layout:

- Desktop: left text column, right workflow snapshot panel
- Mobile: stacked single-column layout

Rules:

- Do not place multiple workflow entry buttons in the hero.
- Do not use the hero to advertise many specific tools.
- Do not reuse the current heavy signal-field visual as the centerpiece.

### 7.2 Workflow Map

Purpose:

- Explain how the platform works as a system.

Structure:

- Input assets
- Understanding and decomposition
- Generation and editing
- Delivery and communication

Rules:

- Show representative capabilities, not the full workflow list.
- Each stage should communicate one sentence of value plus 2-3 representative entries.
- The section should feel like a path, not a card wall.

### 7.3 Result Showcase

Purpose:

- Prove output quality and range.

Recommended result categories:

- Slides
- Figure
- Video or Poster

Rules:

- Show only the strongest representative results.
- Avoid turning the homepage into a large gallery.
- Favor large, clean proof modules over many small thumbnails.

### 7.4 Scenario Section

Purpose:

- Translate platform capability into concrete user situations.

Recommended scenarios:

- Group meeting presentation
- Thesis or defense preparation
- Project proposal and technical roadmap communication
- Research dissemination and explanation
- Literature tracking and rebuttal support

Rules:

- Use user goals and contexts, not internal product terminology.
- This section should bridge from platform message to workflow discovery.

### 7.5 Full Feature Library

Purpose:

- Provide complete workflow discoverability after the platform story is established.

Recommended grouping:

- Create
- Convert
- Explore
- Workspace

Representative mapping:

- Create: Paper2Figure, Paper2PPT, Paper2Poster, Paper2Video
- Convert: PDF2PPT, Image2PPT, Image2DrawIO, PPTPolish
- Explore: Citation, Rebuttal, MindMap, Knowledge Base
- Workspace: Files, history, reuse-oriented entry points

Rules:

- Reuse the existing workflow metadata where possible.
- Reorganize by user intent, not by implementation history.
- Keep the feature library visually subordinate to the hero and workflow map.

## 8. Visual Language

Selected direction:

- Research editorial visual system

Characteristics:

- Light editorial base
- Deep navy text and structure
- Cyan/teal accents aligned with the existing brand palette
- Controlled gradients, not neon-heavy surfaces
- High legibility and strong whitespace discipline

This should feel like:

- A credible research product homepage
- A polished platform surface

This should not feel like:

- A gaming dashboard
- A glowing dark-mode experiment
- A pure feature marketplace

## 9. Motion and Interaction

Motion principles:

- Use restrained motion only.
- Favor reveal, subtle flow, and lightweight hover feedback.
- Remove attention-grabbing ambient effects from the hero background.

CTA behavior:

- Primary CTA scrolls or routes to the workflow map section.
- Secondary CTA scrolls or routes to the result showcase section.

Preview behavior:

- Default to static preview assets or posters.
- Avoid autoplaying multiple heavy videos on initial load.
- Use progressive disclosure for richer previews deeper on the page.

## 10. Responsive Strategy

Desktop:

- Two-column hero
- Workflow map can use horizontal stage layout
- Result showcase can mix one dominant case with smaller companion cases

Mobile:

- Single-column hero stack
- Workflow map becomes a vertical step sequence or stacked cards
- Result showcase becomes horizontally scrollable cards or vertically stacked proofs
- Full feature library becomes grouped accordion or segmented stacked sections

Mobile rules:

- Do not preserve the desktop hero composition literally.
- Do not render a dense multi-column feature wall on small screens.
- Preserve hierarchy before preserving symmetry.

## 11. Implementation Design

Recommended component split:

- `HomePage`
- `HomeHero`
- `WorkflowMapSection`
- `ResultShowcaseSection`
- `ScenarioSection`
- `FeatureLibrarySection`

Current code to evolve:

- `frontend-workflow/src/components/HomePage.tsx`
- `frontend-workflow/src/config/homePageCatalog.ts`
- existing locale files under `frontend-workflow/src/locales`

Implementation principles:

- Keep `HomePage` as a section orchestrator, not a monolith.
- Introduce homepage-specific view models for hero, workflow-map stages, showcase proofs, and scenarios.
- Continue using the current catalog as the source of route-level entries, but stop relying on flat catalog data to define the entire homepage structure.
- Demote the current featured-card grid from the hero area into the later feature library or proof sections.

## 12. Content Strategy

Homepage copy hierarchy:

- Platform language in hero and section headers
- Capability language in workflow map labels
- Scenario language in use-case section
- Feature language only in the full library

Copy rules:

- Repeat the product idea through "research expression" rather than "all workflows".
- Prefer product-value language over navigation language.
- Emphasize editable, reusable, and delivery-ready outcomes.
- Keep hero copy concise; let later sections do the explaining.

## 13. Risks

Risk 1: the page drifts back into a workflow directory.

Mitigation:

- Keep full feature discovery below the first three sections.

Risk 2: the redesign loses too much of the existing product’s technical character.

Mitigation:

- Preserve controlled technical cues inside the workflow snapshot and map modules rather than across the full page.

Risk 3: heavy previews hurt homepage performance.

Mitigation:

- Use static posters or lazy-loaded media for proofs.

Risk 4: mobile layouts become crowded because of the number of workflows.

Mitigation:

- Collapse the full library into grouped sections with stronger prioritization.

## 14. Testing Requirements

- Desktop and mobile visual verification
- CTA routing and in-page navigation behavior
- Graceful fallback when preview assets are missing
- Localization fit for Chinese and English copy lengths
- Performance verification for hero and showcase media loading
- Regression check that all existing workflow destinations remain reachable

## 15. Deliverable Definition

This redesign is complete when:

- The homepage clearly presents Paper2Any as an AI research expression platform.
- A new visitor can understand the product before seeing the full feature library.
- The first visible actions are workflow exploration and proof review, not arbitrary tool selection.
- The old hero visual has been replaced with a clearer, lighter, more editorial system.
- Feature discovery is preserved, but moved to the correct depth in the page.

## 16. Approval State

Validated interactively with the user through:

- Direction selection: platform narrative homepage
- Structure selection: workflow map before result showcase
- Visual selection: research editorial base
- Section-by-section approval of page rhythm, content hierarchy, and implementation boundaries
