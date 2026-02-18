#!/usr/bin/env python3
"""
PR Quality Analyzer
Analyzes pull request metrics for team quality assessment.
"""

import json
import os
import sys
from datetime import datetime, timedelta
from collections import defaultdict
import argparse

try:
    from github import Github
    import pandas as pd
    import matplotlib.pyplot as plt
    import seaborn as sns
    from tabulate import tabulate
except ImportError as e:
    print(f"Error: Missing required package. Run: pip install -r requirements.txt")
    print(f"Details: {e}")
    sys.exit(1)


class PRAnalyzer:
    def __init__(self, config_path='config.json'):
        self.config = self.load_config(config_path)
        self.github = Github(self.config['github_token'])
        self.pr_data = []
        self.team_stats = defaultdict(lambda: {
            'prs_created': 0,
            'prs_reviewed': 0,
            'total_additions': 0,
            'total_deletions': 0,
            'total_comments': 0,
            'review_times': [],
            'pr_sizes': []
        })

    def load_config(self, config_path):
        if not os.path.exists(config_path):
            print(f"Error: Config file '{config_path}' not found.")
            print("Copy config.example.json to config.json and update with your settings.")
            sys.exit(1)
        
        with open(config_path, 'r') as f:
            return json.load(f)

    def fetch_prs(self, start_date=None, end_date=None):
        if not start_date:
            start_date = datetime.now() - timedelta(days=self.config.get('date_range_days', 30))
        if not end_date:
            end_date = datetime.now()

        print(f"\nFetching PRs from {start_date.date()} to {end_date.date()}...")
        
        for repo_name in self.config['repositories']:
            print(f"  Analyzing repository: {repo_name}")
            try:
                repo = self.github.get_repo(repo_name)
                pulls = repo.get_pulls(state='all', sort='updated', direction='desc')
                
                count = 0
                for pr in pulls:
                    if pr.created_at < start_date:
                        break
                    
                    if pr.created_at > end_date:
                        continue
                    
                    if not self.config.get('include_drafts', False) and pr.draft:
                        continue
                    
                    pr_metrics = self.analyze_pr(pr, repo_name)
                    if pr_metrics:
                        self.pr_data.append(pr_metrics)
                        count += 1
                
                print(f"    Found {count} PRs")
            except Exception as e:
                print(f"    Error accessing {repo_name}: {e}")

    def analyze_pr(self, pr, repo_name):
        author = pr.user.login
        
        if self.config.get('exclude_bots', True) and '[bot]' in author:
            return None
        
        team_members = self.config.get('team_members', [])
        if team_members and author not in team_members:
            return None

        time_to_first_review = None
        time_to_merge = None
        
        reviews = list(pr.get_reviews())
        if reviews:
            first_review_time = min(r.submitted_at for r in reviews)
            time_to_first_review = (first_review_time - pr.created_at).total_seconds() / 3600
        
        if pr.merged_at:
            time_to_merge = (pr.merged_at - pr.created_at).total_seconds() / 86400
        
        comments = pr.comments + pr.review_comments
        
        pr_size = pr.additions + pr.deletions
        
        reviewers = set()
        for review in reviews:
            reviewers.add(review.user.login)
        
        self.team_stats[author]['prs_created'] += 1
        self.team_stats[author]['total_additions'] += pr.additions
        self.team_stats[author]['total_deletions'] += pr.deletions
        self.team_stats[author]['pr_sizes'].append(pr_size)
        
        for reviewer in reviewers:
            if reviewer != author:
                self.team_stats[reviewer]['prs_reviewed'] += 1
        
        if time_to_first_review:
            self.team_stats[author]['review_times'].append(time_to_first_review)

        return {
            'repository': repo_name,
            'number': pr.number,
            'title': pr.title,
            'author': author,
            'created_at': pr.created_at,
            'merged_at': pr.merged_at,
            'state': pr.state,
            'additions': pr.additions,
            'deletions': pr.deletions,
            'changed_files': pr.changed_files,
            'comments': comments,
            'commits': pr.commits,
            'reviewers_count': len(reviewers),
            'time_to_first_review_hours': time_to_first_review,
            'time_to_merge_days': time_to_merge,
            'url': pr.html_url
        }

    def generate_report(self):
        if not self.pr_data:
            print("\nNo PR data to analyze. Check your configuration.")
            return

        print("\n" + "="*60)
        print("PR QUALITY REPORT")
        print("="*60)

        df = pd.DataFrame(self.pr_data)
        
        print(f"\nDate Range: {df['created_at'].min().date()} to {df['created_at'].max().date()}")
        print(f"Total PRs Analyzed: {len(df)}")
        
        print("\n--- Overall Metrics ---")
        print(f"Average PR Size: {df['additions'].mean() + df['deletions'].mean():.0f} lines")
        print(f"Average Files Changed: {df['changed_files'].mean():.1f}")
        print(f"Average Commits per PR: {df['commits'].mean():.1f}")
        print(f"Average Comments per PR: {df['comments'].mean():.1f}")
        
        if df['time_to_first_review_hours'].notna().any():
            print(f"Average Time to First Review: {df['time_to_first_review_hours'].mean():.1f} hours")
        
        merged_prs = df[df['merged_at'].notna()]
        if not merged_prs.empty:
            print(f"Merge Rate: {len(merged_prs)/len(df)*100:.1f}%")
            if merged_prs['time_to_merge_days'].notna().any():
                print(f"Average Time to Merge: {merged_prs['time_to_merge_days'].mean():.1f} days")

        print("\n--- Top Contributors ---")
        team_summary = []
        for member, stats in sorted(self.team_stats.items(), 
                                   key=lambda x: x[1]['prs_created'], 
                                   reverse=True):
            avg_pr_size = sum(stats['pr_sizes']) / len(stats['pr_sizes']) if stats['pr_sizes'] else 0
            avg_review_time = sum(stats['review_times']) / len(stats['review_times']) if stats['review_times'] else 0
            
            team_summary.append([
                member,
                stats['prs_created'],
                stats['prs_reviewed'],
                f"{avg_pr_size:.0f}",
                f"{avg_review_time:.1f}h" if avg_review_time else "N/A"
            ])
        
        print(tabulate(team_summary, 
                      headers=['Member', 'PRs Created', 'PRs Reviewed', 'Avg Size', 'Avg Review Time'],
                      tablefmt='simple'))

        print("\n--- PR Size Distribution ---")
        size_ranges = [
            ('Tiny (1-50)', df[(df['additions'] + df['deletions']) <= 50]),
            ('Small (51-200)', df[((df['additions'] + df['deletions']) > 50) & 
                                 ((df['additions'] + df['deletions']) <= 200)]),
            ('Medium (201-500)', df[((df['additions'] + df['deletions']) > 200) & 
                                   ((df['additions'] + df['deletions']) <= 500)]),
            ('Large (501+)', df[(df['additions'] + df['deletions']) > 500])
        ]
        
        for label, subset in size_ranges:
            percentage = len(subset) / len(df) * 100 if len(df) > 0 else 0
            print(f"  {label}: {len(subset)} PRs ({percentage:.1f}%)")

    def create_visualizations(self):
        if not self.pr_data:
            return

        os.makedirs('visualizations', exist_ok=True)
        df = pd.DataFrame(self.pr_data)
        
        sns.set_style('whitegrid')
        
        # PR Size Distribution
        plt.figure(figsize=(10, 6))
        pr_sizes = df['additions'] + df['deletions']
        plt.hist(pr_sizes[pr_sizes <= 1000], bins=30, edgecolor='black')
        plt.xlabel('Lines Changed')
        plt.ylabel('Number of PRs')
        plt.title('PR Size Distribution')
        plt.savefig('visualizations/pr_size_distribution.png', dpi=300, bbox_inches='tight')
        plt.close()
        print("  Saved: visualizations/pr_size_distribution.png")

        # Team Activity
        plt.figure(figsize=(12, 6))
        team_data = [(m, s['prs_created'], s['prs_reviewed']) 
                     for m, s in self.team_stats.items()]
        team_data.sort(key=lambda x: x[1], reverse=True)
        
        members = [t[0] for t in team_data]
        created = [t[1] for t in team_data]
        reviewed = [t[2] for t in team_data]
        
        x = range(len(members))
        width = 0.35
        
        plt.bar([i - width/2 for i in x], created, width, label='PRs Created', alpha=0.8)
        plt.bar([i + width/2 for i in x], reviewed, width, label='PRs Reviewed', alpha=0.8)
        
        plt.xlabel('Team Member')
        plt.ylabel('Count')
        plt.title('Team Activity: PRs Created vs Reviewed')
        plt.xticks(x, members, rotation=45, ha='right')
        plt.legend()
        plt.tight_layout()
        plt.savefig('visualizations/team_activity.png', dpi=300, bbox_inches='tight')
        plt.close()
        print("  Saved: visualizations/team_activity.png")

    def export_csv(self):
        if not self.pr_data:
            return

        os.makedirs('reports', exist_ok=True)
        
        df = pd.DataFrame(self.pr_data)
        df.to_csv('reports/pr_details.csv', index=False)
        print("  Saved: reports/pr_details.csv")
        
        team_df = pd.DataFrame([
            {
                'member': member,
                'prs_created': stats['prs_created'],
                'prs_reviewed': stats['prs_reviewed'],
                'total_additions': stats['total_additions'],
                'total_deletions': stats['total_deletions']
            }
            for member, stats in self.team_stats.items()
        ])
        team_df.to_csv('reports/team_summary.csv', index=False)
        print("  Saved: reports/team_summary.csv")


def main():
    parser = argparse.ArgumentParser(description='Analyze PR quality metrics')
    parser.add_argument('--config', default='config.json', help='Path to config file')
    parser.add_argument('--start-date', help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end-date', help='End date (YYYY-MM-DD)')
    parser.add_argument('--export', choices=['csv'], help='Export format')
    parser.add_argument('--report-only', action='store_true', help='Skip visualizations')
    
    args = parser.parse_args()
    
    start_date = datetime.strptime(args.start_date, '%Y-%m-%d') if args.start_date else None
    end_date = datetime.strptime(args.end_date, '%Y-%m-%d') if args.end_date else None
    
    analyzer = PRAnalyzer(args.config)
    analyzer.fetch_prs(start_date, end_date)
    analyzer.generate_report()
    
    if not args.report_only:
        print("\nGenerating visualizations...")
        analyzer.create_visualizations()
    
    if args.export:
        print("\nExporting data...")
        analyzer.export_csv()
    
    print("\n✓ Analysis complete!")


if __name__ == '__main__':
    main()