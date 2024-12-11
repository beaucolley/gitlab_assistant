#!/usr/bin/env python3

import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt

def main():
    # Sample data: list of issues with creation and completion dates
    issues = [
        {'created': '2023-01-01', 'completed': '2023-01-05'},
        {'created': '2023-01-01', 'completed': '2023-01-06'},
        {'created': '2023-01-02', 'completed': '2023-01-07'},
        {'created': '2023-01-02', 'completed': '2023-01-08'},
        {'created': '2023-01-03', 'completed': '2023-01-09'},
        {'created': '2023-01-03', 'completed': '2023-01-10'},
        {'created': '2023-01-05', 'completed': '2023-01-11'},
        {'created': '2023-01-06', 'completed': '2023-01-12'},
        {'created': '2023-01-01', 'completed': '2023-01-07'},
        {'created': '2023-01-01', 'completed': '2023-01-09'},
        {'created': '2023-01-01', 'completed': '2023-01-10'},
        {'created': '2023-01-01', 'completed': '2023-01-11'},
    ]

    # Convert the list of issues to a DataFrame
    df = pd.DataFrame(issues)
    df['created'] = pd.to_datetime(df['created'])
    df['completed'] = pd.to_datetime(df['completed'])

    # Create a date range from the earliest created date to the latest completed date
    date_range = pd.date_range(start=df['created'].min(), end=df['completed'].max())

    # Initialize lists to store the number of issues created and completed each day
    created_counts = []
    completed_counts = []

    # Count the number of issues created and completed each day
    for date in date_range:
        created_counts.append((df['created'] == date).sum())
        completed_counts.append((df['completed'] == date).sum())

    # Create a DataFrame with the counts
    burndown_df = pd.DataFrame({
        'date': date_range,
        'created': created_counts,
        'completed': completed_counts
    })

    # Calculate the cumulative number of issues open each day
    burndown_df['open'] = burndown_df['created'].cumsum() - burndown_df['completed'].cumsum()

    # Find the maximum number of open issues
    max_open_issues = burndown_df['open'].max()
    print(f"Maximum number of open issues: {max_open_issues}")

    print(burndown_df)

    #Plot the stacked bar chart
    plt.figure(figsize=(10, 6))
    plt.bar(burndown_df['date'], burndown_df['created'], label='Created')
    plt.bar(burndown_df['date'], burndown_df['open'] - burndown_df['created'] + burndown_df['completed'], bottom=burndown_df['created'], label='Open')
    plt.bar(burndown_df['date'], burndown_df['completed'], bottom=burndown_df['open'], label='Completed')
    plt.xlabel('Date')
    plt.ylabel('Number of Issues')
    plt.title('Burndown Chart')
    plt.legend()
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()

    

if __name__ == "__main__":
    main()