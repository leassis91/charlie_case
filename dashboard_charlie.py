
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
import datetime as dt
from streamlit_card import card
import plotly.express as px


# ======================= CONFIG LAYOUT ==================== #
# pandas config
pd.set_option('display.float_format', lambda x: '%.0f' % x)

# streamlit config
st.set_page_config(layout='wide')

# ========================================================== #
st.markdown("<h1 align='center'>Charlie Pricing Dashboard</h2>", unsafe_allow_html=True)
# st.write("")
st.write("<p align='center'> by <a href='https://www.linkedin.com/in/leandrodestefani'>Leandro Destefani</a></p>", unsafe_allow_html=True,
                 # " \t"
                 # "[GitHub](https://github.com/leassis91) "
                 # "  [Mail](leassis.destefani@gmail.com)"
                 )     

# ========================= FUNÇÕES ======================== #
# @st.cache(allow_output_mutation=True)


def get_data(path):
    data = pd.read_excel(path)
    return data


def adjust_columns(df):
    df.drop('prédio', axis=1, inplace=True)
    df = df.sort_values(by='checkin')
    df['dias_reserva'] = (df['checkout'] - df['checkin']).dt.days

    return df


def sidebar_filters(data):
    st.sidebar.title('Dataset Filters')

    # Data Overview Filters
    date_filter = st.sidebar.expander(label='Filtro de Data')
    with date_filter:
            # Date Interval ===================================
        # df['data'] = df['data'].dt.date
        min_date = df['checkin'].min()
        max_date = df['checkin'].max()
        f_date = st.date_input('Select Date:', (min_date, max_date), min_value=min_date, max_value=max_date )
    return data     




def create_features(df):
    """
    Criando features temporais baseadas nos dados de checkin.
    """
    df = df.copy()
#     df['dias_reserva'] = (df['checkout'] - df['checkin']).dt.days
    df['preco_diaria'] = df['receita'] / df['dias_reserva']
    
    df['day_of_week'] = df['checkin'].dt.dayofweek 
    df['day_of_week'] = df['day_of_week'].replace({0: 'Seg', 1:'Ter', 2:'Qua', 3:'Qui', 4:'Sex', 5:'Sab', 6:'Dom'})
    
    # Levando em consideração a info de que sexta e sábado as vendas são maiores
    df['is_sex_sab'] = df['day_of_week'].apply(lambda x: 1 if x in ('Sex', 'Sab') else 0)
    
    df['day'] = df['checkin'].dt.day
    df['month'] = df['checkin'].dt.month
    df['year'] = df['checkin'].dt.year
    df['quarter'] = df['checkin'].dt.quarter # trimeste, 1-4
    df['day_of_year'] = df['checkin'].dt.dayofyear  # dia do ano, 1-365
    df['week_of_year'] = df['checkin'].dt.isocalendar().week  # semana do ano, 1-52
    
    df = df.sort_values(by='checkin')
    
    return df

def data_overview(df):

    c1, c2, c3, c4 = st.columns((2, 2, 2, 2))


    mask_real = df['checkin'] <= '2022-11-14'
    mask_test = df['checkin'] >= '2022-11-15'

    train = df.loc[mask_real]
    test = df.loc[mask_test]

    with c1:
        ticket_medio_antes  = train.groupby('checkin')['preco_diaria'].mean().mean()
        ticket_media_depois = test.groupby('checkin')['preco_diaria'].mean().mean()
        card(title="R$ {:,}".format(ticket_medio_antes), text="ADR Atual", image='')
    with c2:
        card(title="R$ {:,}".format(round(ticket_media_depois, 2)), text="ADR Futuro", image='')
    with c3:
        estadia_antes = train.groupby('checkin')['dias_reserva'].mean().mean()
        card(title=f"{round(estadia_antes, 2)} dias", text="Estadia Atual", image='')
    with c4:
        estadia_depois = test.groupby('checkin')['dias_reserva'].mean().mean()
        card(title=f"{round(estadia_depois, 2)} dias", text="Estadia Futura", image='')



    c1, c2 = st.columns((1, 1))

    with c1:
        fig = px.histogram(df, x= 'dias_reserva', 
             labels={'count': 'Reservas', 'dias_reserva':'Estadia'},
             title='Distribuição da Quantidade de Dias Reservados', 
             color_discrete_sequence=['indianred'])
        fig.update_layout(bargap=0.2)
        c1.plotly_chart(fig, use_containder_width=True)


    with c2:

        
        fig = px.line(
            data_frame=df[['checkin', 'receita']].groupby('checkin').sum(),
            title='Faturamento Diário',
            labels={'value': 'Receita (R$)', 'checkin': 'Dia'}
              )

        c2.plotly_chart(fig, use_containder_width=True)



    c1, c2 = st.columns((2, 2))

    with c1:
        is_fds2 = df[['checkin', 'is_sex_sab']].groupby('checkin').mean()
        aux_diaria3 = df.groupby('checkin')[['preco_diaria', 'dias_reserva', 'day_of_week']].count()
        aux_diaria31 = pd.merge(aux_diaria3, is_fds2, on='checkin')
        fig = px.bar(aux_diaria31[['preco_diaria']], 
            x=aux_diaria31.index.strftime("%d/%m"), 
            y='preco_diaria',
            color=aux_diaria31['is_sex_sab'],
            text_auto=True,
            title='Quantidade de reservas por dia (Amarelo: Sexta e Sábado)',
            labels={'preco_diaria': 'Quantidade de Dias Reservados', 'x': 'Dia'}
                )

        fig.update_layout(bargap=0.2)   
        fig.update_coloraxes(showscale=False)
        # fig.update_traces(showlegend=True)
        fig.update(layout_showlegend=True)  
        c1.plotly_chart(fig, use_containder_width=True)


    with c2:
        maiores_valores = df.groupby('checkin')['preco_diaria'].max()
        sexsab = df.groupby('checkin')['is_sex_sab'].mean()
        fig = px.bar( 
            x=aux_diaria31.index.strftime("%d/%m"), 
            y=maiores_valores, 
            color=sexsab,
            # color_continuous_scale=px.colors.sequential.Cividis_r,
            text_auto=True,
            title='Preço Médio por dia',
            labels={'y': 'Preço Médio', 'x': 'Dia'}
                )

        fig.update_layout(bargap=0.2)
        fig.update_coloraxes(showscale=False)
        # fig.update_traces(showlegend=True)
        fig.update(layout_showlegend=True)  
        c2.plotly_chart(fig, use_containder_width=True)




    c1, c2 = st.columns((2, 2))

    with c1:
        aux4 = df.groupby('day_of_week')['id'].count().reset_index()
        fig = px.bar(aux4, 
                x='day_of_week', 
                y='id',
                color='day_of_week',
                title='Dias Mais Requisitados',
                labels={'id': 'Quantidade de Reservas', 'day_of_week':'Dia da Semana'})
        c1.plotly_chart(fig, use_containder_width=True)


    with c2:
        aux5 = df.groupby('day_of_week')['receita'].sum().reset_index()
        fig = px.bar(aux5, 
                x='day_of_week',
                y='receita',
                title='Dias que mais geram receita',
                color='day_of_week',
                labels={'receita': 'Receita Total (R$)', 'day_of_week':'Dia da Semana'})
        c2.plotly_chart(fig, use_containder_width=True)
        



if __name__ == '__main__':

    file = 'reservation.xlsx'
    df = get_data(file)
    df = adjust_columns(df)
    df = create_features(df)
    # sidebar_filters(df)

    # Dashboard
    data_overview(df)
