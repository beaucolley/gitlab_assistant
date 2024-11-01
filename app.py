#! /usr/bin/env python3

import click
import gitlab
import csv
import json
import logging

# Replace these variables with your own information
GITLAB_URL = 'https://git.web.boeing.com'  # Your GitLab instance URL
PROJECT_ID = '142836'               # The ID of the project you want to access
GROUP_ID = '155309'

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    handlers=[logging.FileHandler("gitlab_assistant.log"), logging.StreamHandler()])

logger = logging.getLogger(__name__)

# Connect to GitLab
gl = gitlab.Gitlab(GITLAB_URL, private_token=PRIVATE_TOKEN)

@click.group()
def cli():
    """Command line tool for managing GitLab issues."""
    pass

@cli.command()
@click.option('--output', default='open_issues.csv', help='Output CSV file for open issues.')
def pull_issues(output):
    """Fetch and export all open issues to a CSV file."""
    # Get the project
    project = gl.projects.get(PROJECT_ID)

    # Get all open issues
    open_issues = project.issues.list(state='opened', get_all=True)

    # Prepare data for CSV
    with open(output, mode='w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['ID', 'iid', 'Title', 'Epic', 'Milestone', 'Iteration', 'Author', 'Created At', 'Description', 'State', 'Weight']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for issue in open_issues:
            logger.info(f"Processing issue {issue.id} - {issue.title}")
            writer.writerow({
                'ID': issue.id,
                'iid': issue.iid,
                'Title': issue.title,
                'Epic': issue.epic["title"],
                'Milestone': issue.milestone["title"],
                'Iteration': issue.iteration,
                'Author': issue.author['name'],
                'Created At': issue.created_at,
                'Description': issue.description,
                'State': issue.state,
                'Weight': issue.weight
            })

    click.echo(f'Open issues exported to {output}')


def get_epic(epic_title):
    epics = gl.groups.get(GROUP_ID).epics.list()
    for epic in epics:
        if epic.title == epic_title:
            return gl.groups.get(GROUP_ID).epics.get(epic.iid)
    logger.error(f'Epic {epic_title} not found.')
    return None


def get_milestone(milestone_title):
    milestones = gl.projects.get(PROJECT_ID).milestones.list()
    for milestone in milestones:
        if milestone.title == milestone_title:
            return gl.groups.get(GROUP_ID).milestones.get(milestone.iid)
    logger.error(f'Milestone {milestone_title} not found.')
    return None

@cli.command()
@click.option('--input', required=True, help='Input CSV file to update issues.')
def update_issues(input):
    """Update issues from a CSV file."""
    # Read the CSV file
    with open(input, mode='r', newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        issues_to_update = [row for row in reader]

    # Get the project
    project = gl.projects.get(PROJECT_ID)

    # Update issues based on the CSV data
    for row in issues_to_update:
        logger.info(f"Processing row {row['ID']} - {row['Title']}")
        issue_id = int(row['iid'])  # Convert ID to integer
        try:
            # Find the issue by ID
            issue = project.issues.get(issue_id)
            issue.title = row['Title']
            issue.description = row['Description']
            issue.state = row['State']  # Note: Changing state may require additional permissions
            issue.weight = row['Weight']

            if row['Epic'] != issue.epic["title"]:
                epic = get_epic(row['Epic'])
                if epic is not None:
                    logger.info(f'Updating Epic for issue ID {issue_id}')
                    ei = epic.issues.create({'issue_id': issue.id})
                    ei.save()

            # issue.milestone = get_milestone(row['Milestone'])
            issue.save()  # Save the changes
            click.echo(f'Updated issue ID {issue_id}')
        except gitlab.exceptions.GitlabGetError:
            click.echo(f'Issue ID {issue_id} not found.')

if __name__ == '__main__':
    cli()
