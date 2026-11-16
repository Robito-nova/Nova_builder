# Design Review Prompts

Use these prompts when reviewing an implemented interface. Report concrete observations, not taste alone.

## Layout and responsiveness

- What is the primary task, and can it be identified immediately?
- Does the page preserve key actions at narrow widths and when zoomed?
- Are there clipped controls, accidental horizontal scrolling, or content hidden behind fixed regions?
- Does content order still make sense when columns collapse?

## Visual system

- Are type roles, spacing, surfaces, borders, and colors consistent?
- Does emphasis lead to the right action, or do secondary accents compete?
- Are long labels, empty states, errors, and realistic content handled without breaking layout?

## Interaction

- Can every action be completed with keyboard and pointer/touch?
- Are focus, disabled, selected, loading, success, and error states visible and understandable?
- Do destructive actions have a safeguard or recovery path?
- Are any controls decorative or nonfunctional despite appearing interactive?

## Accessibility

- Are semantic elements, labels, accessible names, and heading order appropriate?
- Is focus visible and tab order logical?
- Is contrast sufficient, and is status conveyed by more than color?
- Does motion respect reduced-motion preferences?

## Review output

Prioritize findings by severity. For each issue, name the affected component or file, describe the user impact, and suggest the smallest effective correction. Mention viewport sizes, assistive technology, or interaction paths that were not tested.
