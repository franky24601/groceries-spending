import pandas as pd
import plotly.graph_objects as go
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import seaborn as sns
import matplotlib.pyplot as plt

def convert_to_datetime_slash(number):
    """Converts an 8-digit number to a datetime object."""
    try:
        return pd.to_datetime(str(number), format='%m/%d/%Y').date()
    except (ValueError, TypeError):
        return None

def convert_to_datetime_num(number):
    """Converts an 8-digit number to a datetime object."""
    try:
        return pd.to_datetime(str(number), format='%Y%m%d').date()
    except (ValueError, TypeError):
        return None

def convert_to_float(value):
    """Converts a string with a comma decimal to a float, handles other types."""
    try:
        if isinstance(value, str):
            value = value.replace(",", ".")
            return float(value)
        else:
            return float(value)
    except (ValueError, TypeError):
        return None

def create_monthly_totals(df, name_column='Name / Description', date_column='Date', value_column='Amount (EUR)'):
    """
    Filters rows containing 'jumbo', 'dirk', 'albert', or 'Lidl' in the name column,
    and calculates monthly totals for each item and the overall monthly totals.
    """
    filtered_df = df[df[name_column].str.contains('jumbo', case=False, na=False) |
                        df[name_column].str.contains('dirk', case=False, na=False) |
                        df[name_column].str.contains('albert', case=False, na=False) |
                        df[name_column].str.contains('Lidl', case=False, na=False)].copy()

    if filtered_df.empty:
        return pd.DataFrame()

    filtered_df[date_column] = pd.to_datetime(filtered_df[date_column])
    filtered_df['YearMonth'] = filtered_df[date_column].dt.to_period('M')
    filtered_df['Filtered_Name'] = filtered_df[name_column].str.extract(r'(jumbo|dirk|albert|Lidl)', flags=2, expand=False).str.lower()
    monthly_totals = filtered_df.groupby(['YearMonth', 'Filtered_Name'])[value_column].sum().reset_index()
    overall_monthly_totals = filtered_df.groupby('YearMonth')[value_column].sum().reset_index()
    overall_monthly_totals['Filtered_Name'] = 'Total'
    final_monthly_totals = pd.concat([monthly_totals, overall_monthly_totals], ignore_index=True)
    return final_monthly_totals

def comma_to_decimal(series):
    """Converts comma-separated numeric strings in a pandas Series to float numbers."""
    return series.str.replace(',', '.').astype(float)

dfing = pd.read_csv('NL46INGB0002221753_01-06-2024_13-03-2025.csv', sep=';')
dfam = pd.read_csv('activity (2).csv')

dfing['Date'] = dfing['Date'].apply(convert_to_datetime_num)
dfing['Amount (EUR)'] = dfing['Amount (EUR)'].apply(convert_to_float)

dfam['Datum'] = dfam['Datum'].apply(convert_to_datetime_slash)
dfam['Bedrag'] = comma_to_decimal(dfam['Bedrag'])
dfam_renamed = dfam.rename(columns={'Datum': 'Date', 'Omschrijving': 'Name / Description', 'Bedrag': 'Amount (EUR)'})
df_combined = pd.concat([dfing, dfam_renamed], ignore_index=True)

monthly_totals_df = create_monthly_totals(df_combined)
monthly_totals_df['YearMonth'] = monthly_totals_df['YearMonth'].astype(str)

app = dash.Dash(__name__)

app.layout = html.Div(children=[
    html.H1(children='Monthly Spending Dashboard'),

    dcc.Graph(
        id='monthly-totals-chart',
        figure={
            'data': [
                {'x': monthly_totals_df[monthly_totals_df['Filtered_Name'] == 'Total']['YearMonth'],
                 'y': monthly_totals_df[monthly_totals_df['Filtered_Name'] == 'Total']['Amount (EUR)'],
                 'type': 'bar', 'name': 'Total Monthly Spending'}
            ],
            'layout': {
                'title': 'Overall Monthly Spending',
                'xaxis': {'title': 'Month'},
                'yaxis': {'title': 'Total Amount (EUR)'}
            }
        }
    ),
    dcc.Graph(
        id='store-monthly-totals-chart',
        figure=go.Figure(data=[
            go.Bar(name=name, x=monthly_totals_df[monthly_totals_df['Filtered_Name'] == name]['YearMonth'],
                   y=monthly_totals_df[monthly_totals_df['Filtered_Name'] == name]['Amount (EUR)'])
            for name in monthly_totals_df['Filtered_Name'].unique() if name != 'Total'
        ], layout=go.Layout(title='Monthly Spending Per Store', xaxis_title='Month', yaxis_title='Amount (EUR)'))
    )

])

if __name__ == '__main__':
    app.run(debug=True)