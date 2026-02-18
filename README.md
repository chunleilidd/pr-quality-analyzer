# PR Quality Analyzer

Analyze your team's pull request quality with comprehensive metrics and insights.

## Features

- **PR Size Analysis**: Track lines of code changed per PR
- **Review Time Metrics**: Measure time to first review and time to merge
- **Code Review Quality**: Analyze review comment depth and engagement
- **Approval Patterns**: Track approval rates and reviewer participation
- **Trend Analysis**: Visualize PR quality trends over time
- **Team Leaderboards**: Compare team member contributions and review activity

## Metrics Tracked

### Per Pull Request
- Lines added/removed
- Files changed
- Time to first review
- Time to merge
- Number of review comments
- Number of reviewers
- Number of commits
- Review iterations

### Per Team Member
- PRs created
- PRs reviewed
- Average PR size
- Average review turnaround time
- Review comment quality score
- Approval rate

## Setup

### Prerequisites

- Python 3.8+
- GitHub Personal Access Token with `repo` scope

### Installation

```bash
pip install -r requirements.txt
```

### Configuration

1. Copy the example config:
```bash
cp config.example.json config.json
```

2. Edit `config.json` with your settings:
```json
{
  "github_token": "your_github_token_here",
  "repositories": [
    "owner/repo1",
    "owner/repo2"
  ],
  "team_members": [
    "username1",
    "username2",
    "username3"
  ],
  "date_range_days": 30
}
```

## Usage

### Analyze PRs

```bash
python pr_analyzer.py
```

This will:
1. Fetch PRs from configured repositories
2. Calculate quality metrics
3. Generate a report in `reports/` directory
4. Create visualizations in `visualizations/` directory

### Generate Report

```bash
python pr_analyzer.py --report-only
```

### Export Data

```bash
python pr_analyzer.py --export csv
```

## Output

### Console Report

You'll see a summary like:

```
=== PR Quality Report ===
Date Range: 2026-01-17 to 2026-02-17

Team Overview:
- Total PRs: 45
- Average PR Size: 234 lines
- Average Time to Review: 4.2 hours
- Average Time to Merge: 1.3 days

Top Contributors:
1. alice (15 PRs, 25 reviews)
2. bob (12 PRs, 18 reviews)
3. charlie (10 PRs, 22 reviews)
```

### Visualization Charts

- `pr_size_distribution.png` - Histogram of PR sizes
- `review_time_trends.png` - Time-series of review times
- `team_activity.png` - Bar chart of team member activity
- `quality_scores.png` - Radar chart of quality metrics

### CSV Export

- `reports/pr_details.csv` - Detailed PR metrics
- `reports/team_summary.csv` - Team member summaries

## Advanced Usage

### Custom Date Range

```bash
python pr_analyzer.py --start-date 2026-01-01 --end-date 2026-01-31
```

### Filter by Team Member

```bash
python pr_analyzer.py --author username
```

### Include Draft PRs

```bash
python pr_analyzer.py --include-drafts
```

## Metrics Explanation

### Quality Score

A composite score (0-100) based on:
- PR size (smaller is better, 20%)
- Review time (faster is better, 20%)
- Review engagement (more comments = better, 30%)
- Test coverage (if CI data available, 30%)

### Review Engagement

Measures the quality of code review through:
- Number of review comments
- Depth of review threads
- Use of suggestions vs. plain comments
- Response time to reviews

## Contributing

Contributions welcome! Please open an issue or PR.

## License

MIT License - feel free to use and modify for your team's needs.