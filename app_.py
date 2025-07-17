# app.py

import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import plotly.express as px

st.set_page_config(layout="wide")
st.title("🌍 Dashboard Interativo - Saúde Mental no Mundo (1990–2019)")

# === Carregamento de dados ===
@st.cache_data
def load_data():
    df1 = pd.read_csv("1-saude_mental.csv")
    df2 = pd.read_csv("2-dalys.csv")
    df5 = pd.read_csv("5-gap_tratamento.csv")
    for df in [df1, df2, df5]:
        if "Code" in df.columns:
            df.drop(columns=["Code"], inplace=True)
    return df1, df2, df5

df1, df2, df5 = load_data()

def load_forecast():
    return pd.read_csv("previsoes_prevalencia_por_pais_2020_2040.csv")

df_forecast = load_forecast()

# === SIDEBAR ===
st.sidebar.header("🎛️ Filtros")
countries = sorted(
    list(
        set(df1["Entity"].unique()) & 
        set(df2["Entity"].unique()) & 
        set(df_forecast["Entity"].unique())
    )
)
selected_countries = st.sidebar.multiselect("Selecione os países", countries, default=["Brazil", "India", "United States"])
year_range = st.sidebar.slider("Intervalo de anos", 1990, 2019, (1995, 2019), 1)

transtornos_disponiveis = {
    'Depressão': 'Depressive disorders (share of population) - Sex: Both - Age: Age-standardized',
    'Ansiedade': 'Anxiety disorders (share of population) - Sex: Both - Age: Age-standardized',
    'Esquizofrenia': 'Schizophrenia disorders (share of population) - Sex: Both - Age: Age-standardized',
    'Bipolaridade': 'Bipolar disorders (share of population) - Sex: Both - Age: Age-standardized',
    'Transtornos Alimentares': 'Eating disorders (share of population) - Sex: Both - Age: Age-standardized'
}
selected_transtornos = st.sidebar.multiselect(
    "Selecione os transtornos mentais",
    options=list(transtornos_disponiveis.keys()),
    default=['Depressão', 'Ansiedade']
)

# === TABS ===
tab1, tab2 = st.tabs(["📈 Saúde Mental", "📊 Comparação de Transtornos (2020–2040)"])

# === TAB 1 ===
with tab1:
    st.subheader("📊 Evolução da Prevalência dos Transtornos Selecionados")

    if len(selected_transtornos) == 0:
        st.warning("Selecione pelo menos um transtorno na barra lateral.")
    else:
        filtered_df = df1[(df1["Entity"].isin(selected_countries)) &
                        (df1["Year"].between(*year_range))]
        if filtered_df.empty:
            st.warning("Nenhum dado disponível para os países e intervalo de anos selecionados.")
        else:
        # seu código para gráficos


            col1, col2 = st.columns(2)
            for i, transtorno in enumerate(selected_transtornos[:2]):
                coluna_transtorno = transtornos_disponiveis[transtorno]
                with (col1 if i == 0 else col2):
                    fig, ax = plt.subplots(figsize=(6, 4))
                    sns.lineplot(data=filtered_df, x="Year", y=coluna_transtorno, hue="Entity", ax=ax)
                    ax.set_title(f"{transtorno} — Prevalência ao longo dos anos")
                    ax.set_ylabel("Prevalência (%)")
                    ax.grid(True)
                    st.pyplot(fig)

    st.markdown("---")
    st.subheader("🌍 Mapas de Calor - Prevalência em 2019 dos Transtornos Selecionados")

    if len(selected_transtornos) == 0:
        st.warning("Selecione pelo menos um transtorno para exibir os mapas.")
    else:
        mapa_cols = st.columns(len(selected_transtornos[:3]))  # até 3 mapas por vez

        for i, transtorno in enumerate(selected_transtornos[:3]):
            coluna_dados = transtornos_disponiveis[transtorno]

            mapa_df = df1[(df1["Year"] == 2019) & (df1["Entity"].isin(selected_countries))][["Entity", coluna_dados]].copy()
            mapa_df.columns = ["Country", "Prevalence"]

            fig = px.choropleth(
                mapa_df,
                locations="Country",
                locationmode="country names",
                color="Prevalence",
                color_continuous_scale="Plasma",
                title=f"{transtorno} - Prevalência em 2019 (%)",
                hover_name="Country"
            )
            fig.update_layout(margin={"r": 0, "t": 40, "l": 0, "b": 0})
            mapa_cols[i].plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    st.subheader("🌐 Tendência Global da Prevalência")

    transtornos_padrao = selected_transtornos if selected_transtornos else ['Depressão', 'Ansiedade']
    colunas_grafico = [transtornos_disponiveis[t] for t in transtornos_padrao]
    df_global_avg = df1.groupby("Year")[colunas_grafico].mean().reset_index()
    rename_dict = {transtornos_disponiveis[t]: t for t in transtornos_padrao}
    df_global_avg.rename(columns=rename_dict, inplace=True)

    df_global_long = df_global_avg.melt(id_vars="Year", value_vars=transtornos_padrao,
                                   var_name="Transtorno", value_name="Prevalência (%)")

    fig_global = px.line(
        df_global_long,
        x="Year",
        y="Prevalência (%)",
        color="Transtorno",
        title="Tendência Global da Prevalência de Transtornos Mentais"
    )

    st.plotly_chart(fig_global, use_container_width=True)

    st.subheader("📌 Correlação entre Prevalência e DALYs")
    df_merge = pd.merge(df1, df2, on=["Entity", "Year"])
    df_corr = df_merge[(df_merge["Entity"].isin(selected_countries)) &
                       (df_merge["Year"].between(*year_range))]

    x = transtornos_disponiveis["Depressão"]
    y = "DALYs (rate) - Sex: Both - Age: Age-standardized - Cause: Depressive disorders"

    fig2, ax2 = plt.subplots(figsize=(8, 6))
    sns.scatterplot(data=df_corr, x=x, y=y, hue="Entity", ax=ax2)
    ax2.set_title("Prevalência vs. DALYs - Depressão")
    ax2.set_xlabel("Prevalência (%)")
    ax2.set_ylabel("DALYs por 100 mil")
    ax2.grid(True)
    st.pyplot(fig2)

    st.subheader("🚫 Lacuna no Tratamento em Saúde Mental")
    df5["Treatment gap (%)"] = 100 - df5["Potentially adequate treatment, conditional"].fillna(0)
    st.markdown("#### 🌐 Top 10 países com maior média de falta de tratamento")
    top10_gap = df5.groupby("Entity")["Treatment gap (%)"].mean().sort_values(ascending=False).head(10)
    st.bar_chart(top10_gap)

# === TAB 2 ===
with tab2:
    st.subheader("📊previsão de prevalência(2020–2040)")

    paises = sorted(df_forecast['Entity'].unique())
    pais_selecionado = st.selectbox("🌍 Selecione o país", paises, index=paises.index("Brazil") if "Brazil" in paises else 0)


    transtornos_prev = {
        "Depressão": "Pred_Prevalence_Depression",
        "Ansiedade": "Pred_Prevalence_Anxiety",
        "Esquizofrenia": "Pred_Prevalence_Schizophrenia",
        "Transtorno Bipolar": "Pred_Prevalence_Bipolar",
        "Transtornos Alimentares": "Pred_Prevalence_Eating"
    }

    col3, col4 = st.columns(2)
    with col3:
        transtorno_prev_1 = st.selectbox("🔹 Transtorno 1 (Prevalência)", list(transtornos_prev.keys()), index=0, key="prev1")
    with col4:
        transtorno_prev_2 = st.selectbox("🔸 Transtorno 2 (Prevalência)", list(transtornos_prev.keys()), index=1, key="prev2")

    if transtorno_prev_1 == transtorno_prev_2:
        st.warning("Selecione dois transtornos diferentes para comparar a prevalência.")
    else:
        col_prev_1 = transtornos_prev[transtorno_prev_1]
        col_prev_2 = transtornos_prev[transtorno_prev_2]

        df_prev_pais = df_forecast[df_forecast["Entity"] == pais_selecionado][["Year", col_prev_1, col_prev_2]].copy()
        df_prev_pais.rename(columns={col_prev_1: transtorno_prev_1, col_prev_2: transtorno_prev_2}, inplace=True)
        df_prev_melted = df_prev_pais.melt(id_vars="Year", var_name="Transtorno", value_name="Prevalência Prevista")

        fig_prev = px.line(
            df_prev_melted,
            x="Year",
            y="Prevalência Prevista",
            color="Transtorno",
            title=f"Prevalência Prevista: {transtorno_prev_1} vs {transtorno_prev_2} em {pais_selecionado} (2020–2040)",
            markers=True
        )
        st.plotly_chart(fig_prev, use_container_width=True)

        with st.expander("📋 Ver dados da previsão de prevalência"):
            st.dataframe(df_prev_pais, use_container_width=True)