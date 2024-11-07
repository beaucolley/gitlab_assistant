#! /usr/bin/env python3

import click
import gitlab
import csv
import json
import logging
import os
import configparser

# Load configuration from config file
config = configparser.ConfigParser()
config.read(os.path.join(os.path.dirname(__file__), 'config.ini'))

GITLAB_URL = config['gitlab']['url']
PROJECT_ID = config['gitlab']['project_id']
GROUP_ID = config['gitlab']['group_id']
PRIVATE_TOKEN = config['gitlab']['access_token']

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
        fieldnames = ['id', 'iid', 'title', 'epic', 'milestone', 'iteration', 'author', 'created_at', 'description', 'state', 'weight']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for issue in open_issues:
            logger.info(f"Processing issue {issue.id} - {issue.title}")
            writer.writerow({
                'id': issue.id,
                'iid': issue.iid,
                'title': issue.title,
                'epic': issue.epic["title"] if issue.epic else '',
                'milestone': issue.milestone["title"] if issue.milestone else '',
                'iteration': issue.iteration if 'iteration' in issue.attributes else '',
                'author': issue.author['name'],
                'created_at': issue.created_at,
                'description': issue.description,
                'state': issue.state,
                'weight': issue.weight if 'weight' in issue.attributes else ''
            })

    click.echo(f'Open issues exported to {output}')


def get_epic(epic_title):
    epics = gl.groups.get(GROUP_ID).epics.list()
    logger.debug(f'epics: {epics}')
    for epic in epics:
        if epic.title == epic_title:
            return gl.groups.get(GROUP_ID).epics.get(epic.iid)
    logger.error(f'epic {epic_title} not found.')
    return None


def get_milestone(milestone_title):
    milestones = gl.projects.get(PROJECT_ID).milestones.list()
    for milestone in milestones:
        if milestone.title == milestone_title:
            return gl.groups.get(GROUP_ID).milestones.get(milestone.iid)
    logger.error(f'milestone {milestone_title} not found.')
    return None

def update_issue(issue, row):
    logger.info(f"Updating issue ID {issue.iid} - {issue.title}")
    issue_updated = False
    
    for key, value in row.items():
        if key in issue.attributes and str(getattr(issue, key, '')).strip() != str(value).strip() and value != "":
            if key == 'author':
                continue

            if key == 'epic':
                # Remove epic from issue if csv value is empty or different
                if  value == "" or (issue.epic is not None and value != issue.epic["title"]):
                    logger.info(f"Removing epic {issue.epic['title']}")
                    issue.epic = None
                    issue_updated = True
                    continue
                
                # Check if epic is already set
                if issue.epic is not None and value == issue.epic["title"]:
                    continue

                # Set epic
                epic = get_epic(value)
                if epic is not None:
                    epic.issues.create({'issue_id': issue.id})
                    logger.info(f"Added issue to epic {value}")
                continue
                
            logger.info(f"Updating {key} from {getattr(issue, key, '')} to {value}")
            setattr(issue, key, value)
            issue_updated = True

    if issue_updated:
        issue.save()


def create_issue(row):
    logger.info(f"Creating new issue {row['title']}")
    new_issue_data = {
        'title': row['title'],
        'description': row['description'],
        'state': row['state'],
        'weight': row['weight']
    }

    if row['epic']:
        epic = get_epic(row['epic'])
        if epic is not None:
            new_issue_data['epic_id'] = epic.id

    if row['milestone']:
        milestone = get_milestone(row['milestone'])
        if milestone is not None:
            new_issue_data['milestone_id'] = milestone.id

    project = gl.projects.get(PROJECT_ID)
    project.issues.create(new_issue_data)


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
        issue_id = row['iid']  # Convert ID to integer

        if issue_id == "":
            create_issue(row)
        else:
            try:
                issue = project.issues.get(int(issue_id))
                update_issue(issue, row)
            except gitlab.exceptions.GitlabGetError:
                click.echo(f'Issue ID {issue_id} not found.')
        


if __name__ == '__main__':
    cli()
