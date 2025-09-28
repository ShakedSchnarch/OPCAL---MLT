# Documentation and Comment Standard

The goal is to keep reference documentation, tutorials, and in-code explanations aligned so external labs can understand and adapt the tool quickly.

## Python docstrings
- Use Google-style docstrings for all public modules, classes, and functions.
- Start with a short summary sentence in the imperative mood (≤ 88 characters when possible).
- Leave a blank line between the summary and the remainder of the docstring.
- Order sections as needed using the following headings:
  - `Args:` for positional and keyword parameters.
  - `Keyword Args:` if keyword-only arguments warrant separate emphasis.
  - `Returns:` even when the function returns `None` (state it explicitly).
  - `Raises:` for user-facing exceptions.
  - `Yields:` for generators.
  - `Notes:` for background, equations, or domain-specific caveats.
  - `Examples:` for short code snippets that aid comprehension.
- Align type hints with the signature; docstrings should clarify intent, constraints, and side effects rather than restating types verbatim.
- Prefer descriptive phrasing over abbreviations unless they are domain-standard (e.g., ΔF/F).

## Module docstrings
- Begin each Python module with a concise summary (one or two sentences).
- Include a short paragraph when additional context is necessary (e.g., layout of collaborating modules).
- Avoid ASCII art import listings unless the module layout is non-trivial.

## Inline comments
- Use comments sparingly for non-obvious control flow, numerical methods, or side effects.
- When explaining domain logic, phrase comments as guidance ("Explain why" instead of "Repeat what").
- Remove outdated or redundant comments encountered during refactors.

## Markdown documentation
- Prefer H1 for page title, H2 for major sections, and use thematic breaks (`---`) when helpful.
- Keep tables and lists concise; break up dense paragraphs with subheadings if they exceed ~6 sentences.
- Cross-link related documents using relative paths (e.g., `[API](API.md)`).

## Changelog entries
- Follow [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) sections (`Added`, `Changed`, `Fixed`, etc.).
- Mention documentation updates explicitly when they modify user-facing behaviour or interfaces.

## Contribution checklist
- Confirm new functions/classes include Google-style docstrings when they are part of the public API.
- Run `ruff check` and `pytest` before opening a pull request; the linters enforce docstring quotes and spacing.
- When touching multiple modules, keep documentation updates in the same commit so reviewers can trace intent easily.
