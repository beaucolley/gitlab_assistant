#! /usr/bin/env python3

import click
import gitlab
import csv
import json
import logging
import os
import configparser
from collections import defaultdict
import pdb
import re

# Load configuration from config file
config = configparser.ConfigParser()
config.read(os.path.join(os.path.dirname(__file__), 'config.ini'))

GITLAB_URL = config['gitlab']['url']
PROJECT_ID = config['gitlab']['project_id']
GROUP_ID = config['gitlab']['group_id']
PRIVATE_TOKEN = config['gitlab']['access_token']

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
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
        fieldnames = ['id', 'iid', 'title', 'epic', 'milestone', 'iteration', 'labels', 'author', 'created_at', 'description', 'state', 'weight']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for issue in open_issues:
            logger.info(f"Processing issue {issue.id} - {issue.title}")
            # pdb.set_trace()
            writer.writerow({
                'id': issue.id,
                'iid': issue.iid,
                'title': issue.title,
                'epic': issue.epic["title"] if issue.epic else '',
                'milestone': issue.milestone["title"] if issue.milestone else '',
                'iteration': issue.iteration['start_date'] if issue.attributes['iteration'] is not None else '',
                'labels': ', '.join(issue.labels),
                'author': issue.author['name'],
                'created_at': issue.created_at,
                'description': issue.description,
                'state': issue.state,
                'weight': issue.weight if 'weight' in issue.attributes else ''
            })

    click.echo(f'Open issues exported to {output}')


def get_iteration_id(start_date):
    iterations = gl.groups.get(GROUP_ID).iterations.list(get_all=True)
    for iteration in iterations:
        # pdb.set_trace()
        logger.info(iteration.attributes['start_date'])
        if start_date.strip() == iteration.attributes['start_date']:
            return iteration.iid
    logger.error(f"Iteration with start date {start_date} not found")
    pass


def get_epic(epic_title):
    epics = gl.groups.get(GROUP_ID).epics.list(get_all=True, state='opened')
    logger.debug(f'epics: {epics}')
    for epic in epics:
        if epic.title.strip().lower() == epic_title.strip().lower():
            return gl.groups.get(GROUP_ID).epics.get(epic.iid)
    logger.error(f'epic {epic_title} not found.')
    return None


def get_milestone_id(milestone_title):
    milestones = gl.groups.get(GROUP_ID).milestones.list(state='active', get_all=True)
    logger.info(f'milestones: {milestones}')

    for milestone in milestones:
        if milestone.title.strip().lower() == milestone_title.strip().lower():
            return milestone.get_id()
    logger.error(f'milestone {milestone_title} not found.')
    return None


def update_issue(issue, row):
    logger.info(f"Updating issue ID {issue.iid} - {issue.title}")
    issue_updated = False

    for key, value in row.items():
        if key in issue.attributes and str(getattr(issue, key, '')).strip() != str(value).strip() and value != "":
            if key == 'author':
                continue

            if key == 'iteration':
                continue

            if key == 'labels':
                continue

            if key == 'epic':
                # Remove epic from issue if csv value is empty or different
                if value == "" or (issue.epic is not None and value != issue.epic["title"]):
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

            if key == 'milestone':
                # Remove milestone from issue if csv value is empty or different
                if value == "" or (issue.milestone is not None and value != issue.milestone["title"]):
                    logger.info(f"Removing milestone {issue.milestone['title']}")
                    issue.milestone = None
                    issue_updated = True
                    continue

                # Check if milestone is already set
                if issue.milestone is not None and value == issue.milestone["title"]:
                    continue

                # Set milestone
                milestone_id = get_milestone_id(value)
                issue.milestone_id = milestone_id
                issue_updated = True
                continue

            logger.info(f"Updating {key} from {getattr(issue, key, '')} to {value}")
            setattr(issue, key, value)
            issue_updated = True

    if issue_updated:
        # pdb.set_trace()
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
        milestone_id = get_milestone_id(row['milestone'])
        if milestone_id is not None:
            new_issue_data['milestone_id'] = milestone_id

    project = gl.projects.get(PROJECT_ID)
    logger.info(f"Creating new issue {new_issue_data}") 
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
            except gitlab.exceptions.GitlabGetError as e:
                click.echo(f'Issue ID {issue_id} not found - {e}')
            except gitlab.exceptions.GitlabUpdateError as e:
                click.echo(f'Issue ID {issue_id} could not be updated - {e}')

@cli.command()
@click.option('--input', required=True, help='Input CSV file to determine issues to keep.')
def close_issues(input):
    """Close issues that are not present in the input CSV file."""
    # Read the CSV file
    with open(input, mode='r', newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        issue_ids_to_keep = {row['iid'] for row in reader}

    # Get the project
    project = gl.projects.get(PROJECT_ID)

    # Get all issues
    all_issues = project.issues.list(get_all=True)

    # Determine issues to close
    issues_to_close = [issue for issue in all_issues if str(issue.iid) not in issue_ids_to_keep]

    # Print issues to close
    if issues_to_close:
        click.echo('The following issues will be closed:')
        for issue in issues_to_close:
            click.echo(f"ID: {issue.iid}, Title: {issue.title}")

        # Confirm closure
        confirmation = click.prompt('Type "close" to confirm closure of the above issues', type=str)
        if confirmation.lower() == 'close':
            for issue in issues_to_close:
                logger.info(f"Closing issue ID {issue.iid} - {issue.title}")
                issue.state_event = 'close'
                issue.save()
            click.echo('Issues not present in the CSV have been closed.')
        else:
            click.echo('Closure aborted.')
    else:
        click.echo('No issues to close.')


def format_time(hours: float) -> str:
    hours_int = int(hours)
    minutes = int((hours - hours_int) * 60)
    return f'{hours_int}h{minutes}m'


@cli.command()
def log_time():
    """Log time spent on an issue."""

    # Get the project
    project = gl.projects.get(PROJECT_ID)

    active_labels = ['STATUS::Doing', 'Testing']

    # Get the issue
    issues = project.issues.list(state='opened', get_all=True)

    # Get the specific issue with the title 'USER ALLOCATION'
    user_allocation_issue = None
    for issue in issues:
        if issue.title == 'USER ALLOCATION':
            user_allocation_issue = issue
            break

    if user_allocation_issue:
        logger.info(f"Found issue with title 'USER_ALLOCATION': ID {user_allocation_issue.iid}")
        logger.info(user_allocation_issue.description)
    else:
        logger.error("Issue with title 'USER_ALLOCATION' not found.")

    # Parse the description for user tags and allocation percentages
    user_allocations = {}
    allocation_pattern = re.compile(r'@([^\n]+)')

    if user_allocation_issue:
        matches = allocation_pattern.findall(user_allocation_issue.description)
        print(matches)

        for match in matches:
            username, allocation = match.split('=')
            user_allocations[username.strip()] = float(allocation.strip())

    logger.info(f"User allocations: {user_allocations}")

    # Filter issues by active labels
    filtered_issues = [issue for issue in issues if any(label in issue.labels for label in active_labels)]

    issues_by_user = defaultdict(list)

    for issue in filtered_issues:
        # print(issue.title)
        assignees = issue.assignees
        for assignee in assignees:
            issues_by_user[assignee['username']].append(issue)

    for user, issues in issues_by_user.items():
        time_per_ticket = format_time(7.6/len(issues)*user_allocations[user])
        logger.info(f"{len(issues)} assigned to {user} - logging {time_per_ticket} for each issue.")

        for issue in issues:
            logger.info(f"{issue.iid} - {issue.title} - {issue.labels}")
            issue.add_spent_time(time_per_ticket)


if __name__ == '__main__':
    cli()
