import dash
from dash import dcc, html, dash_table
from dash.dependencies import Input, Output
import plotly.express as px
import plotly.graph_objs as go
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Código de generación de datos (proporcionado)
np.random.seed(42)
date_range = pd.date_range(start='2023-01-01', end='2023-12-31', freq='h')
categories = ['Electrónica', 'Ropa', 'Libros', 'Alimentos']
products = {
    'Electrónica': ['Portátil', 'Smartphone', 'Tablet', 'Auriculares'],
    'Ropa': ['Camiseta', 'Jeans', 'Vestido', 'Zapatos'],
    'Libros': ['Ficción', 'No ficción', 'Libro de texto', 'Revista'],
    'Alimentos': ['Frutas', 'Verduras', 'Snacks', 'Bebidas']
}

def factor_estacional(date):
    day_of_year = date.dayofyear
    return 1 + 0.5 * np.sin(2 * np.pi * day_of_year / 365)

def factor_diario(date):
    day_of_week = date.dayofweek
    if day_of_week < 5:  # Día laborable
        return 1 + 0.2 * np.random.random()
    else:  # Fin de semana
        return 1.5 + 0.3 * np.random.random()

def factor_horario(hour):
    if 9 <= hour <= 18:  # Horas de trabajo
        return 1 + 0.5 * np.sin(np.pi * (hour - 9) / 9)
    elif 0 <= hour < 6:  # Madrugada
        return 0.2 + 0.1 * np.random.random()
    else:  # Tarde
        return 0.5 + 0.3 * np.random.random()

data = []
for category in categories:
    category_factor = np.exp(np.random.uniform(0.10, 3.00))
    for date in date_range:
        season = factor_estacional(date)
        daily = factor_diario(date)
        hourly = factor_horario(date.hour)
    
        for product in products[category]:
            product_factor = np.random.uniform(0.7, 1.3)
            
            base_quantity = np.random.randint(0, 10)
            quantity = int(base_quantity * season * daily * hourly * category_factor * product_factor)
         
            if category == 'Electrónica':
                price = np.random.uniform(100, 2000)
            elif category == 'Ropa':
                price = np.random.uniform(20, 200)
            elif category == 'Libros':
                price = np.random.uniform(10, 50)
            else:  # Alimentos
                price = np.random.uniform(5, 30)

            data.append({
                    'Fecha': date,
                    'Categoría': category,
                    'Producto': product,
                    'Cantidad': quantity,
                    'Precio': price,
                    'Ingresos': quantity * price
                })

df = pd.DataFrame(data)
df['Día'] = df['Fecha'].dt.day_name()
df['Hora'] = df['Fecha'].dt.hour
df.head()

app = dash.Dash(__name__)
server = app.server 

app.layout = html.Div(style={'fontFamily': 'Arial', 'padding': '20px'}, children=[
    html.H1("Dashboard de análisis de ventas E-commerce"),

    html.Div([
        html.Div([
            html.Label("Rango de Fechas:"),
            dcc.DatePickerRange(
                id='date-range', 
                min_date_allowed=df['Fecha'].min(),
                max_date_allowed=df['Fecha'].max(),
                start_date=df['Fecha'].min(),
                end_date=df['Fecha'].max()
            )
        ], style={'width': '33%', 'display': 'inline-block'}),

        html.Div([
            html.Label("Categoría:"),
            dcc.Dropdown(
                id='category-dropdown', 
                options=[{'label': i, 'value': i} for i in df['Categoría'].unique()] + [{'label': 'Todas', 'value': 'all'}],
                value='all'
            )
        ], style={'width': '33%', 'display': 'inline-block'}),

        html.Div([
            html.Label("Métrica:"),
            dcc.RadioItems(
                id='metric-radio', 
                options=[{'label': 'Ingresos', 'value': 'Ingresos'}, {'label': 'Cantidad', 'value': 'Cantidad'}],
                value='Ingresos',
                inline=True
            )
        ], style={'width': '33%', 'display': 'inline-block'})
    ], style={'padding': '20px', 'backgroundColor': "#f9f9f9"}),

    dcc.Graph(id='sales-time-series'), 
    
    html.Div([
        dcc.Graph(id='category-pie-chart', style={'width': '49%', 'display': 'inline-block'}),
        dcc.Graph(id='sales-heatmap', style={'width': '49%', 'display': 'inline-block'})
    ]),

    html.H3("Tabla de productos"),
    dash_table.DataTable(
    id='top-products-table',
    style_table={
        'height': '400px',      
        'overflowY': 'auto',      
        'overflowX': 'auto'       
    },
    fixed_rows={'headers': True}, 
    style_cell={
        'fontFamily': 'Arial',
        'padding': '10px',
        'minWidth': '150px', 'width': '150px', 'maxWidth': '150px', 
    },
    style_header={
        'fontFamily': 'Arial',
        'fontWeight': 'bold',
        'backgroundColor': '#2c3e50',
        'color': 'white'
    },
    page_action='none', )
    
    ])

@app.callback(
    [Output('sales-time-series', 'figure'),
     Output('category-pie-chart', 'figure'),
     Output('sales-heatmap', 'figure'),
     Output('top-products-table', 'data'),
     Output('top-products-table', 'columns')],
    [Input('date-range', 'start_date'),
     Input('date-range', 'end_date'),
     Input('category-dropdown', 'value'),
     Input('metric-radio', 'value')]
)
def actualizar_dashboard(start_date, end_date, selected_cat, metric):
    # Filtrado de datos
    dff = df[(df['Fecha'] >= pd.to_datetime(start_date)) & 
             (df['Fecha'] <= pd.to_datetime(end_date))]
    
    if selected_cat != 'all':
        dff = dff[dff['Categoría'] == selected_cat]

    if dff.empty:
        return {}, {}, {}, [], []

    # Serie Temporal
    df_ts = dff.groupby(dff['Fecha'].dt.date)[metric].sum().reset_index()
    df_ts['Tendencia'] = df_ts[metric].rolling(window=7).mean()
    fig_ts = px.line(
        df_ts, x='Fecha', 
        y=metric, 
        title=f"<b>Evolución de {metric.lower()}</b>",
        color_discrete_sequence=['#636EFA'],
        labels={
        'Fecha': 'Día de Venta', 
        metric: f'Total de {metric}'}
        )
    fig_ts.update_traces(name=f"Ventas diarias", showlegend=True)
    fig_ts.add_scatter(
        x=df_ts['Fecha'], 
        y=df_ts['Tendencia'], 
        mode='lines', 
        name='Promedio (7d)',
        line=dict(color='#EF553B', width=2, dash='dot',)
    )
    fig_ts.update_layout(
        font_family="Arial",
        xaxis_title="Fecha",
        yaxis_title=metric,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    # Gráfico Circular
    df_pie = dff.groupby('Categoría')[metric].sum().reset_index()
    fig_pie = px.pie(df_pie, values=metric, names='Categoría', title=f"<b>Distribución por categoría: {metric.lower()}</b>")
    fig_pie.update_layout(font_family="Arial")

    # Heatmap
    orden_dias = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    df_heat = dff.groupby(['Día', 'Hora'])[metric].mean().reset_index()
    fig_heat = px.density_heatmap(df_heat, x='Hora', y='Día', z=metric, 
                                  category_orders={'Día': orden_dias},
                                  title=f"<b>Promedio de {metric.lower()} por hora y día</b>",
                                  color_continuous_scale='Viridis',
                                  labels={metric: f'Suma de {metric}', 
                                  'Hora': 'Hora',
                                  'Día': 'Día de la semana'})
    fig_heat.update_layout(coloraxis_colorbar_title=f"Suma de {metric.lower()}",font_family="Arial")

    # Tabla
    df_top = dff.groupby(['Producto', 'Categoría'])[metric].sum().reset_index()
    df_top = df_top.sort_values(by=metric, ascending=False)
    
    columns = [{"name": i, "id": i} for i in df_top.columns]
    data = df_top.to_dict('records')

    return fig_ts, fig_pie, fig_heat, data, columns

if __name__ == '__main__':
    app.run(debug=False) 