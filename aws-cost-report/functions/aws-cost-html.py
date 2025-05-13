import pandas as pd
import datetime
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from dateutil.relativedelta import relativedelta
import random
import os
import numpy as np

def generate_mock_data(months_back=6):
    """Generate mock AWS cost data for testing"""
    # Create date range
    end_date = datetime.date.today().replace(day=1)
    date_list = []
    
    for i in range(months_back):
        date = (end_date - relativedelta(months=i)).strftime('%Y-%m-%d')
        date_list.append(date)
    
    date_list.reverse()  # Start from oldest date
    
    # Create mock services with color mapping
    services_with_colors = {
        'Amazon Elastic Compute Cloud': '#FF9900',  # EC2 - Orange
        'Amazon Simple Storage Service': '#3B48CC',  # S3 - Blue
        'Amazon RDS Service': '#2E73B8',  # RDS - Light Blue
        'AWS Lambda': '#FF5252',  # Lambda - Red
        'Amazon DynamoDB': '#5A45AA',  # DynamoDB - Purple
        'AWS CloudTrail': '#2ECC71',  # CloudTrail - Green
        'Amazon CloudWatch': '#3498DB',  # CloudWatch - Sky Blue
        'Amazon Route 53': '#F39C12',  # Route 53 - Yellow
        'AWS Key Management Service': '#9B59B6',  # KMS - Violet
        'Amazon Virtual Private Cloud': '#1ABC9C',  # VPC - Teal
        'Amazon ElastiCache': '#E74C3C',  # ElastiCache - Dark Red
        'Amazon SageMaker': '#8E44AD'  # SageMaker - Dark Purple
    }
    
    services = list(services_with_colors.keys())
    
    # Create mock accounts
    accounts = [
        '123456789012 (Production)',
        '234567890123 (Development)',
        '345678901234 (Staging)',
        '456789012345 (Data Processing)',
        '567890123456 (Analytics)',
        '678901234567 (ML Training)',
        '789012345678 (Web Services)',
        '890123456789 (Infrastructure)'
    ]
    
    # Generate service data
    service_data = []
    
    # Base costs for services (to make data realistic)
    service_base_costs = {
        service: random.uniform(100, 5000) for service in services
    }
    
    for date in date_list:
        for service in services:
            # Create some variation in costs over time with a growth trend
            month_index = date_list.index(date)
            trend_factor = 1.0 + (month_index * 0.05)  # 5% growth trend
            variation = random.uniform(0.8, 1.2) * trend_factor
            cost = service_base_costs[service] * variation
            
            service_data.append({
                'Service': service,
                'Period': date,
                'Cost': round(cost, 2),
                'Unit': 'USD',
                'Color': services_with_colors[service]
            })
    
    # Generate account data
    account_data = []
    
    # Base costs for accounts
    account_base_costs = {
        account: random.uniform(1000, 10000) for account in accounts
    }
    
    for date in date_list:
        for account in accounts:
            # Create some variation in costs over time
            month_index = date_list.index(date)
            trend_factor = 1.0 + (month_index * 0.03)  # 3% growth trend
            variation = random.uniform(0.85, 1.15) * trend_factor
            cost = account_base_costs[account] * variation
            
            account_data.append({
                'Account': account,
                'Period': date,
                'Cost': round(cost, 2),
                'Unit': 'USD'
            })
    
    return service_data, account_data, services_with_colors

def create_cost_report_with_mock_data(months_back=6):
    """Create an interactive HTML cost report using mock data"""
    print("Generating mock AWS cost data...")
    service_data, account_data, service_colors = generate_mock_data(months_back)
    
    # Convert to DataFrames
    service_df = pd.DataFrame(service_data)
    account_df = pd.DataFrame(account_data)
    
    print(f"Generated mock data for {len(service_df['Service'].unique())} services " +
          f"and {len(account_df['Account'].unique())} accounts " +
          f"over {months_back} months.")
    
    # Create a pivot table for services
    service_pivot = service_df.pivot_table(
        index='Service', 
        columns='Period', 
        values='Cost',
        aggfunc='sum'
    ).fillna(0)
    
    # Create a pivot table for accounts
    account_pivot = account_df.pivot_table(
        index='Account', 
        columns='Period', 
        values='Cost',
        aggfunc='sum'
    ).fillna(0)
    
    # Calculate total column for each service and account
    service_pivot['Total'] = service_pivot.sum(axis=1)
    account_pivot['Total'] = account_pivot.sum(axis=1)
    
    # Sort by total cost
    service_pivot = service_pivot.sort_values('Total', ascending=False)
    account_pivot = account_pivot.sort_values('Total', ascending=False)
    
    # Get date columns (exclude 'Total')
    date_columns = [col for col in service_pivot.columns if col != 'Total']
    
    # Format month labels
    month_labels = []
    for month in date_columns:
        if '-' in month:
            parts = month.split('-')
            if len(parts) == 3:
                month_labels.append(f"{parts[1]}/{parts[0][-2:]}")  # MM/YY format
            else:
                month_labels.append(month)
        else:
            month_labels.append(month)
    
    # Ensure the output directory exists
    output_dir = 'aws_cost_report'
    os.makedirs(output_dir, exist_ok=True)
    
    # Save data to Excel for reference
    excel_path = os.path.join(output_dir, 'aws_cost_report.xlsx')
    with pd.ExcelWriter(excel_path) as writer:
        service_pivot.to_excel(writer, sheet_name='Services')
        account_pivot.to_excel(writer, sheet_name='Accounts')
    
    print(f"Report data saved to Excel: {excel_path}")
    
    # Create interactive Plotly dashboard with multiple charts
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=("Monthly Cost by Service", "Top 10 Services by Total Cost", 
                        "Monthly Cost Trend", "Cost by Account"),
        specs=[[{"colspan": 2}, None], [{"type": "xy"}, {"type": "domain"}]],
        vertical_spacing=0.10,
        horizontal_spacing=0.05
    )
    
    # Prepare data for stacked bar chart
    # Get top services by total cost
    top_n_services = 8
    stack_data = service_pivot.drop('Total', axis=1).copy()
    
    # If there are more services than top_n, group the rest as 'Other'
    if len(stack_data) > top_n_services:
        top_services = stack_data.iloc[:top_n_services]
        other_services = stack_data.iloc[top_n_services:].sum()
        other_row = pd.DataFrame([other_services], index=['Other Services'])
        stack_data = pd.concat([top_services, other_row])
    
    # Colors for the services
    colors = []
    for service in stack_data.index:
        if service == 'Other Services':
            colors.append('#CCCCCC')  # Gray for 'Other'
        else:
            colors.append(service_colors.get(service, '#AAAAAA'))
    
    # Chart 1: Stacked bar chart for monthly cost by service
    for i, service in enumerate(stack_data.index):
        fig.add_trace(
            go.Bar(
                x=month_labels,
                y=stack_data.loc[service].values,
                name=service,
                marker_color=colors[i],
                hovertemplate='Month: %{x}<br>Cost: $%{y:,.2f}<br>Service: ' + service
            ),
            row=1, col=1
        )
    
    # Chart 2: Bar chart for top 10 services by total cost
    top_10_services = service_pivot['Total'].nlargest(10)
    service_colors_list = [service_colors.get(service, '#AAAAAA') for service in top_10_services.index]
    
    fig.add_trace(
        go.Bar(
            x=top_10_services.values,
            y=top_10_services.index,
            orientation='h',
            marker_color=service_colors_list,
            hovertemplate='Service: %{y}<br>Total Cost: $%{x:,.2f}'
        ),
        row=2, col=1
    )
    
    # Chart 3: Pie chart for cost by account
    top_5_accounts = account_pivot['Total'].nlargest(5)
    other_accounts_total = account_pivot['Total'].sum() - top_5_accounts.sum()
    
    if other_accounts_total > 0:
        # Add "Other Accounts" to the pie chart
        account_values = list(top_5_accounts.values) + [other_accounts_total]
        account_labels = list(top_5_accounts.index) + ['Other Accounts']
    else:
        account_values = list(top_5_accounts.values)
        account_labels = list(top_5_accounts.index)
    
    fig.add_trace(
        go.Pie(
            values=account_values,
            labels=account_labels,
            hovertemplate='Account: %{label}<br>Cost: $%{value:,.2f}<br>Percentage: %{percent}'
        ),
        row=2, col=2
    )
    
    # Chart 4: Line chart for monthly cost trend (overlay on stacked bar)
    monthly_totals = stack_data.sum()
    
    fig.add_trace(
        go.Scatter(
            x=month_labels,
            y=monthly_totals.values,
            mode='lines+markers',
            name='Total Cost',
            line=dict(color='black', width=3),
            marker=dict(size=8, color='black'),
            hovertemplate='Month: %{x}<br>Total Cost: $%{y:,.2f}'
        ),
        row=1, col=1
    )
    
    # Update layout and formatting
    fig.update_layout(
        title='AWS Cost Explorer Dashboard',
        barmode='stack',
        height=800,
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5
        ),
        hoverlabel=dict(
            bgcolor="white",
            font_size=12,
            font_family="Arial"
        ),
        template="plotly_white"
    )
    
    # Format the axes for the charts
    fig.update_xaxes(title_text='Month', row=1, col=1)
    fig.update_yaxes(title_text='Cost (USD)', row=1, col=1, tickprefix='$', tickformat=',.0f')
    
    fig.update_xaxes(title_text='Cost (USD)', row=2, col=1, tickprefix='$', tickformat=',.0f')
    fig.update_yaxes(title_text='Service', row=2, col=1)
    
    # Save the interactive dashboard as an HTML file
    html_path = os.path.join(output_dir, 'aws_cost_explorer_dashboard.html')
    fig.write_html(html_path, include_plotlyjs=True, full_html=True)
    
    print(f"Interactive dashboard saved as: {html_path}")
    print(f"All files are in the '{output_dir}' folder.")

if __name__ == "__main__":
    create_cost_report_with_mock_data(months_back=6)