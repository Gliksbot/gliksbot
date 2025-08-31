# Copilot Coding Agent Instructions for gliksbot

## Overview
This repository uses GitHub Copilot Coding Agent to automate and streamline code changes, reviews, and feature implementation. Follow these best practices to ensure smooth collaboration and effective use of Copilot Coding Agent.

## Best Practices

### 1. Issue and PR Descriptions
- Clearly describe the problem, feature, or change requested.
- Include acceptance criteria, expected behavior, and any relevant context.
- For UI/UX changes, provide wireframes, screenshots, or concise summaries.

### 2. Task Breakdown
- Break large features into smaller, actionable tasks or issues.
- Use checklists for multi-step changes.

### 3. Code Quality
- Follow repository coding standards and style guides.
- Write clear, maintainable code with comments where necessary.
- Prefer existing libraries and frameworks when possible.

### 4. Testing
- Include or update tests for new features and bug fixes.
- Ensure all tests pass before merging.

### 5. Error Handling
- UI errors should be isolated to their respective components (e.g., LLM slot boxes).
- System should remain operational as long as Dexter’s slot is configured correctly.

### 6. UI/UX Guidelines
- Chat pane must always allow communication with Dexter.
- LLM slot panes display real-time output or error states; errors do not interrupt Dexter or main chat.
- Model configuration tab should use intuitive selectors for slot and parameter editing.

### 7. Review and Merge
- Use Copilot Coding Agent to automate code reviews and PR merges when possible.
- Address feedback promptly and document major decisions in PR comments.

## References
- [Best practices for Copilot coding agent in your repository](https://gh.io/copilot-coding-agent-tips)

---

For questions or improvements to these instructions, open an issue or pull request.
