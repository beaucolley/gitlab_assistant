#!/usr/bin/env python3

import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt

issues = [
    {'created_at': '2023-01-01', 'updated_at': '2023-01-03', 'closed_at': '2023-01-05', 'state': 'closed'},
    {'created_at': '2023-01-02', 'updated_at': '2023-01-04', 'closed_at': '2023-01-06', 'state': 'closed'},
    {'created_at': '2023-01-03', 'updated_at': '2023-01-05', 'closed_at': '2023-01-07', 'state': 'closed'},
    {'created_at': '2023-01-04', 'updated_at': '2023-01-06', 'closed_at': '2023-01-08', 'state': 'closed'},
    {'created_at': '2023-01-05', 'updated_at': '2023-02-07', 'closed_at': '2023-02-09', 'state': 'closed'},
    {'created_at': '2023-01-06', 'updated_at': '2023-02-08', 'closed_at': '2023-02-10', 'state': 'closed'},
    {'created_at': '2023-01-07', 'updated_at': '2023-03-09', 'closed_at': '2023-03-11', 'state': 'closed'},
    {'created_at': '2023-01-08', 'updated_at': '2023-03-10', 'closed_at': '2023-03-12', 'state': 'closed'},
    {'created_at': '2023-01-09', 'updated_at': '2023-03-11', 'closed_at': '2023-03-13', 'state': 'closed'},
    {'created_at': '2023-01-10', 'updated_at': '2023-03-12', 'closed_at': '2023-03-14', 'state': 'closed'},
    {'created_at': '2023-02-01', 'updated_at': '2023-03-03', 'closed_at': '2023-03-05', 'state': 'closed'},
    {'created_at': '2023-02-02', 'updated_at': '2023-03-04', 'closed_at': '2023-03-06', 'state': 'closed'},
    {'created_at': '2023-02-03', 'updated_at': '2023-03-05', 'closed_at': '2023-03-07', 'state': 'closed'},
    {'created_at': '2023-02-04', 'updated_at': '2023-03-06', 'closed_at': '2023-03-08', 'state': 'closed'},
    {'created_at': '2023-02-05', 'updated_at': '2023-03-07', 'closed_at': '2023-03-09', 'state': 'closed'},
    {'created_at': '2023-02-06', 'updated_at': '2023-03-08', 'closed_at': '2023-03-10', 'state': 'closed'},
    {'created_at': '2023-02-07', 'updated_at': '2023-02-09', 'closed_at': '2023-02-11', 'state': 'closed'},
    {'created_at': '2023-02-08', 'updated_at': '2023-02-10', 'closed_at': '2023-02-12', 'state': 'closed'},
    {'created_at': '2023-03-01', 'updated_at': '2023-03-03', 'closed_at': '2023-03-05', 'state': 'closed'},
    {'created_at': '2023-03-02', 'updated_at': '2023-03-04', 'closed_at': '2023-03-06', 'state': 'closed'},
    {'created_at': '2023-03-03', 'updated_at': '2023-03-05', 'closed_at': None, 'state': 'open'},
    {'created_at': '2023-03-04', 'updated_at': '2023-03-06', 'closed_at': None, 'state': 'open'},
    {'created_at': '2023-03-05', 'updated_at': '2023-03-07', 'closed_at': None, 'state': 'open'},
    {'created_at': '2023-03-06', 'updated_at': '2023-03-08', 'closed_at': None, 'state': 'open'},
]

def issues_to_df(issues):
    df = pd.DataFrame(issues)
    df['created_at'] = pd.to_datetime(df['created_at'])
    df['closed_at'] = pd.to_datetime(df['closed_at'])
    df['state'] = df['state'].astype(str)
    return df

def create_burndown_chart(burndown_df):
    # Plot the stacked bar chart
    plt.figure(figsize=(10, 6))
    plt.bar(burndown_df.index, burndown_df['created'], label='Created')
    plt.bar(burndown_df.index, burndown_df['open'] - burndown_df['created'] + burndown_df['completed'], bottom=burndown_df['created'], label='Open')
    plt.bar(burndown_df.index, burndown_df['completed'], bottom=burndown_df['open'], label='Completed')
    plt.xlabel('Date')
    plt.ylabel('Number of Issues')
    plt.title('Burndown Chart')
    plt.legend()
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()

def main():
    # Convert the list of issues to a DataFrame
    df = issues_to_df(issues)

    print(df)

    # Create a date range from the earliest created date to the latest completed date

    # date_range = pd.date_range(start=df['created'].min(), end=df['completed'].max(), freq='W-MON')
    date_range = pd.date_range(start=df['created_at'].min(), end=df['closed_at'].max(), freq='MS')

    print(date_range)

    # Initialize lists to store the number of issues created and completed each day
    created_counts = []
    completed_counts = []
    open_counts = []

    for date in date_range:
        created_count = df[(df['created_at'] >= date) & (df['created_at'] < date + pd.offsets.MonthBegin(1))].shape[0]
        completed_count = df[(df['closed_at'] >= date) & (df['closed_at'] < date + pd.offsets.MonthBegin(1))].shape[0]
        open_count = df[(df['created_at'] < date + pd.offsets.MonthBegin(1))].shape[0]
        print(f"date: {date}, created: {created_count}, completed: {completed_count}, open: {open_count}")
        open_counts.append(open_count)
        created_counts.append(created_count)
        completed_counts.append(completed_count)

    print(created_counts)
    print(completed_counts)
    print(open_counts)

    return

    burndown_df = pd.DataFrame({
        'date': date_range,
        'created': created_counts,
        'completed': completed_counts
    }).set_index('date')

    burndown_df['open'] = burndown_df['created'].cumsum() - burndown_df['completed'].cumsum()

    print(burndown_df)

    create_burndown_chart(burndown_df)


if __name__ == "__main__":
    main()