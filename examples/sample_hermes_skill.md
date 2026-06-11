---
name: web-search
description: Search the web using DuckDuckGo or Google. Falls back when web_search tool is unavailable.
version: 1.2.0
author: Hermes Community
license: MIT
platforms: [macos, linux]

metadata:
  hermes:
    tags: [search, web, research]
    category: productivity
    fallback_for_toolsets: [web]
    fallback_for_tools: [web_search]
    related_skills: [arxiv, research-paper]

required_environment_variables:
  - name: DDG_API_KEY
    prompt: DuckDuckGo API key (optional, enhances results)
    help: Get one at https://duckduckgo.com/api
    required_for: enhanced search results

required_credential_files: []

---

# Web Search

## When to Use

Use this skill when the user asks to search the web, look up information, or find current data about a topic. This skill activates as a fallback when the built-in `web_search` tool is unavailable.

## Quick Reference

| Method | Command | Notes |
|--------|---------|-------|
| DuckDuckGo | `!ddg <query>` | Default, no API key needed |
| Google (via DDG) | `!ddg -g <query>` | Better for recent results |
| Lucky | `!ddg -l <query>` | Go to first result |

## Procedure

1. Parse the user's search query
2. Run the appropriate search command
3. Parse the results (JSON format)
4. Summarize the top 5-10 results
5. Present findings with URLs

## Pitfalls

- Rate limiting: DDG free tier allows ~30 requests/minute
- JSON parsing: handle malformed responses gracefully
- Encoding: some results may contain Unicode characters

## Verification

Confirm the search returned results by checking the result count in the JSON response.
