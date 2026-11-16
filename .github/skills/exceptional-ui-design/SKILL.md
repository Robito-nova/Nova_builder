---
name: exceptional-ui-design
description: Create, improve, or review polished, modern, accessible and visually coherent websites and GUI interfaces in any frontend framework or language. Use when implementing pages, apps, dashboards, design systems, responsive layouts, or UI components, or when asked to improve visual quality.
---

# Exceptional UI Design

Design and implement interfaces that feel intentional, clear, distinctive, and complete. Treat visual design, content, behavior, accessibility, and implementation quality as one problem. These instructions are stack-agnostic: use the project's existing framework, styling system, components, and conventions.

## Working principles

- Start from the user's goal, audience, content, and context. Build the smallest coherent experience that serves that goal.
- Read the existing project structure, design tokens, components, and conventions before changing files. Reuse the established stack and patterns unless they prevent the requested outcome.
- Make deliberate choices. A strong interface has a clear visual point of view, a consistent system, and a small number of meaningful accents.
- Prefer a finished, usable screen over decorative complexity. Content and interaction should explain what the product does.
- Do not invent product facts, metrics, customer logos, testimonials, or functionality. Use realistic sample content only when needed, and make its illustrative nature clear.
- Keep implementation maintainable and responsive. Avoid unnecessary dependencies and broad rewrites.
- If critical product requirements are missing, make a reasonable, reversible assumption and state it briefly. Ask only when the ambiguity would materially change the design or behavior.

## Design process

1. **Understand the task.** Identify the primary user, their main action, supporting information, target devices, and any supplied brand or design references. Inspect relevant existing files.
2. **Set the direction.** Pick a concise visual concept appropriate to the product (for example, editorial, calm utility, premium commerce, or expressive creator tool). Define hierarchy, density, tone, and one or two signature details. Avoid generic template styling.
3. **Map the experience.** Establish page regions, navigation, primary and secondary actions, content order, and important empty/loading/error/success states. Keep the primary action visually unmistakable.
4. **Build a compact visual system.** Define or reuse tokens for color, type, spacing, radii, borders, shadows, and layout widths. Apply them consistently rather than styling each element in isolation.
5. **Implement in layers.** Create semantic structure and responsive layout first; refine typography and spacing next; then surfaces, details, and interactions. Keep components cohesive and reusable where repetition or behavior warrants it.
6. **Review the rendered result when a preview is available.** Check a narrow and a wide viewport. Correct clipping, awkward wrapping, weak hierarchy, uneven spacing, and controls that are hard to use. If visual preview is unavailable, inspect the implementation carefully and say that the rendered layout was not visually checked.
7. **Finish with a quality pass.** Use the checklist below. Run project checks only when requested or when needed to diagnose an observed implementation issue; report what was actually checked.

## Visual hierarchy and composition

- Give each screen one clear focal point and a predictable reading path. Use size, weight, contrast, placement, and whitespace to show what matters first.
- Group related content and separate unrelated regions. Use alignment and a consistent grid to create order; do not force every screen into identical card grids.
- Use whitespace as structure. Give major sections enough breathing room while keeping related labels and controls compact.
- Make density fit the task: dashboards can be information-rich but need strong grouping; marketing pages need a clear narrative and restrained calls to action; forms need focus and legibility.
- Use imagery, illustration, gradients, borders, and shadows only when they support meaning or the chosen art direction. Avoid decoration that competes with content.
- Keep content width readable. Use a deliberate max-width for long text and let data-heavy areas use their needed space.

## Typography

- Establish a type scale with distinct roles for display/title, section headings, body, labels, and supporting metadata. Avoid many near-identical sizes.
- Choose fonts that fit the brand and are available in the project. Prefer a restrained family pairing; use system fonts when no font asset is provided rather than adding a remote dependency without need.
- Set line-height and measure for comfortable reading. Body copy should not be too small or too wide; headings should wrap gracefully on mobile.
- Use weight and color to distinguish hierarchy, not uppercase or letter spacing everywhere. Reserve all-caps and tight tracking for short labels when suitable.
- Make numeric and tabular content easy to compare; align values consistently where useful.

## Spacing, shape, and surfaces

- Use a consistent spacing scale (for example, steps around 4–8 px and multiples) and apply it to layout, component padding, and gaps.
- Keep component internals aligned: labels, values, icons, and actions should share clear edges and baselines.
- Use a limited radius vocabulary. Shape should reinforce the product's character, not vary randomly.
- Build depth with a restrained surface hierarchy (page background, content surface, overlay). Do not place every item in its own card.
- Use shadows sparingly and consistently. Borders and surface contrast are often clearer than heavy shadows.

## Color system

- Define semantic roles such as page, surface, raised surface, primary text, muted text, border, primary action, focus, success, warning, and danger.
- Choose a coherent palette with one primary accent and a limited set of supporting colors. Use neutrals to preserve legibility and let meaningful actions stand out.
- Ensure text, icons, control boundaries, and focus indicators have sufficient contrast in each theme. Never communicate status through color alone; pair it with text, shape, or an icon.
- Support an existing light/dark theme if the project has one. If designing both, check each semantic role in both themes instead of simply inverting colors.
- Avoid low-contrast gray-on-gray, excessive neon, and large decorative gradients that reduce readability.

## Responsive behavior

- Design for content reflow, not a shrunken desktop canvas. Use flexible sizing, intrinsic content, and breakpoints based on when the composition stops working.
- Preserve the primary action and important content at small widths. Reorder or simplify secondary regions deliberately.
- Prevent horizontal overflow, clipped controls, and text hidden behind fixed headers or footers. Allow tables and dense data to adapt with a clear strategy.
- Make navigation appropriate to the viewport while keeping its labels and destinations understandable.
- Check touch targets and spacing on touch screens. Do not rely on hover to reveal essential information or actions.
- Respect zoom and larger text settings; avoid fixed heights that cut off content.

## Accessibility and semantics

- Use native semantic elements and controls: headings in logical order, landmarks, buttons for actions, links for navigation, and labels associated with form fields.
- Ensure the full experience works with keyboard input. Provide visible focus styles, sensible tab order, and no keyboard traps.
- Use accessible names for icon-only controls; hide purely decorative icons from assistive technology. Add useful alternative text for meaningful images.
- Provide clear labels, instructions, and error feedback. Do not rely on placeholder text as the only label.
- Respect reduced-motion preferences. Keep animation brief and purposeful; never make motion necessary to understand status or use the interface.
- Use accessible contrast and status cues, and avoid conveying meaning through color alone.
- For custom widgets, implement their expected keyboard and assistive technology behavior; prefer native controls when they can meet the need.

## Interaction and state quality

- Every visible interactive element should work and communicate its purpose. Avoid dead buttons, fake links, and controls that look actionable but do nothing.
- Define default, hover, focus-visible, pressed/active, disabled, and selected states where applicable. Include loading, empty, error, and success states for asynchronous or data-driven flows.
- Make state changes perceivable with concise feedback. Preserve entered data when validation fails and explain how to fix the issue.
- Prevent accidental destructive actions; use clear confirmation or undo patterns when appropriate.
- Keep transitions short and subtle. Avoid gratuitous parallax, bouncing, autoplay, or motion that slows common tasks.
- Use consistent interaction patterns across similar components and do not make hover-only functionality essential.

## Component quality and implementation

- Match the project's conventions and use existing components or tokens before creating new ones. Avoid duplicate primitives with subtly different behavior.
- Give components one clear responsibility and meaningful names. Keep content, state, and presentation understandable in the chosen framework.
- Use data-driven rendering for repeated items when it improves consistency. Avoid overabstracting a one-off element.
- Preserve semantic HTML and accessible behavior when using component libraries. Do not choose a library solely for appearance.
- Use stable layout techniques and avoid brittle absolute positioning for primary content. Avoid arbitrary magic numbers when a token or layout rule is clearer.
- Keep responsive styles and interaction states close to the component or system that owns them. Do not add global styles that unintentionally affect unrelated screens.
- Use real project assets when available. Do not hotlink arbitrary images or introduce external font/image services without a clear need and project fit.

## Anti-patterns to avoid

- Generic, indistinguishable template layouts with no connection to the product or user.
- Excessive cards, pills, gradients, glass effects, shadows, borders, or decorative icons.
- Several competing accent colors or inconsistent spacing, radii, typography, and layouts.
- Tiny low-contrast text, long unbroken lines, cramped controls, or headings that wrap awkwardly.
- Desktop-only layouts, fixed-width canvases, horizontal overflow, and mobile layouts that hide core actions.
- Placeholder-only forms, unlabeled icon buttons, missing focus states, and color-only status indicators.
- Fake functionality, empty links, inert buttons, and unhandled loading/error/empty states.
- Unnecessary animations, auto-playing media, or motion that ignores reduced-motion preferences.
- Replacing the existing stack or rewriting unrelated areas just to achieve a visual effect.

## Final quality checklist

- [ ] The screen's purpose and primary action are obvious at a glance.
- [ ] The visual direction suits the product and is consistent across the screen.
- [ ] Typography, color, spacing, shape, and surface levels follow a deliberate system.
- [ ] Content is realistic, readable, well grouped, and not crowded or needlessly padded.
- [ ] Layout reflows cleanly on narrow and wide screens without clipped content or accidental overflow.
- [ ] Interactive controls have clear labels and complete focus, active, disabled, and relevant data states.
- [ ] Keyboard use, semantic structure, accessible names, contrast, and reduced-motion needs are addressed.
- [ ] All visible actions do what their labels promise; errors and feedback are understandable.
- [ ] Existing project conventions and assets are respected; complexity and dependencies are justified.
- [ ] Any unverified visual or behavioral assumptions are stated clearly in the handoff.

For additional review prompts and responsive checks, see [design-review.md](design-review.md).
