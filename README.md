# Novaterra Competitive Intelligence Agent

This repository contains a simple competitive‑intelligence agent designed for
Novaterra’s marketing team.  Its primary goal is to automatically gather
publicly available signals about the activity of Mauritian smart‑city projects
that compete directly with Beau Plan.  Every Monday at 06:00 UTC a GitHub
Action executes a Python script which searches the web for news, product
announcements, pricing or promotional changes, press releases, event
announcements and other weak signals related to each competitor.  New items
detected during the run are written to a dated report in the `reports/`
directory and recorded in a persistent `memory.json` file to avoid duplicate
notifications.

> **Phase 1:** The current implementation writes Markdown reports into the
> repository.  After a few weeks of validation the agent can be extended to
> publish findings into a Monday.com board.  No external servers or paid
> infrastructure are required – the entire pipeline runs on GitHub Actions and
> the repository itself becomes the versioned storage for historical memory and
> reports.

## Repository structure

```
novaterra-veille/
├── .github/workflows/veille.yml   # weekly cron to run the agent
├── agent.py                       # main Python script
├── competitors.json               # fixed list of competitors to monitor
├── memory.json                    # persistent memory of previously seen items
├── reports/                       # directory containing dated Markdown reports
├── requirements.txt               # Python dependencies
└── README.md                      # this file
```

### Competitors list

The **`competitors.json`** file defines the set of smart‑city projects to
monitor.  Each entry has a `name`, one or more `keywords` used for search, and
an optional `website` field.  Feel free to expand the keyword list for more
precise queries.  Only competitors in Mauritius are included, as they compete
directly with Beau Plan.  The current list comprises:

- **Moka Smart City** (ENL)
- **Uniciti Smart City** (Medine, Flic‑en‑Flac)
- **Mont Choisy Smart City**
- **Cap Tamarin** (Medine)
- **Côte d’Or City** (Landscope, public)
- **Trianon Smart City** (ENL)
- **Telfair / Vivéa Business Park** (extension of Moka, ENL)

### Memory file

The **`memory.json`** file stores the list of links previously reported for
each competitor.  When the agent discovers a search result not present in
memory it is considered a new item.  After writing the weekly report the
memory is updated and committed back to the repository so that subsequent runs
can ignore already‑notified links.

### Reports

Reports are saved under the `reports/` directory with names in the
`YYYY‑MM‑DD.md` format.  They are grouped by competitor and list each new
item’s title, URL and an automatically assigned category (e.g. product
announcement, pricing & commercial, press & communication, or weak signal).

### Extending the agent

This code is intentionally simple and should be considered a starting point.
Possible future improvements include:

- Using a more robust web‑search API (e.g. SerpAPI) instead of scraping
  DuckDuckGo results.
- Fetching the destination pages to extract publication dates and richer
  context.
- Implementing natural‑language classification instead of simple keyword
  heuristics.
- Posting results to a Monday.com board via the API.

Contributions and refinements are welcome!