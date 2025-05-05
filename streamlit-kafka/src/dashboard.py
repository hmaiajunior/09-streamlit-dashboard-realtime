import pandas as pd
import streamlit as st
from consumer import get_message  # Importando a função do Consumer
from producer import regions, vendors

# Configuração do Streamlit
st.set_page_config(page_title="Workshop Streamlit - Real Time Dashboard", page_icon="📈", layout="wide")

st.title("📊 Workshop Streamlit - Real Time Dashboard")

# Placeholder para atualização dinâmica
dashboard_placeholder = st.empty()

# Configuração da barra lateral para filtros
with st.sidebar:
    st.header("🔍 Filtros")
    vendor_filter = st.multiselect("Vendedor", vendors)
    region_filter = st.multiselect("Região", regions)

# Criar um DataFrame inicial vazio
orders_df = pd.DataFrame(columns=["order_id", "order_date", "product_id", "region", "vendor", "quantity", "unit_price", "total_price"])

# Loop para atualização contínua
while True:
    # Obtém nova mensagem do Kafka
    new_data = get_message()

    if new_data:
        # Transformar nova mensagem em DataFrame e adicionar aos dados existentes
        new_order_df = pd.DataFrame([new_data])
        new_order_df["order_date"] = pd.to_datetime(new_order_df["order_date"])
        orders_df = pd.concat([orders_df, new_order_df], ignore_index=True)

    # Aplicar filtros
    if vendor_filter:
        orders_df = orders_df[orders_df["vendor"].isin(vendor_filter)]
    if region_filter:
        orders_df = orders_df[orders_df["region"].isin(region_filter)]

    # Atualizar interface
    with dashboard_placeholder.container():
        # Métricas principais
        orders_col, itens_col, ticket_col, total_col = st.columns(4)

        with orders_col:
            quantity = len(orders_df)
            st.metric(label="📦 Pedidos", value=f"{quantity:,}")

        with itens_col:
            itens = orders_df["quantity"].sum()
            st.metric(label="📊 Itens Vendidos", value=f"{itens:,}")

        with ticket_col:
            ticket = orders_df["total_price"].mean() if not orders_df.empty else 0
            st.metric(label="💰 Ticket Médio", value=f"R$ {ticket:,.2f}")

        with total_col:
            total = orders_df["total_price"].sum() if not orders_df.empty else 0
            st.metric(label="📈 Total de Vendas", value=f"R$ {total:,.2f}")

        # Gráficos
        st.header("📊 Análise por Região e Vendedor")
        order_barchat, region_barchart = st.columns(2)

        with order_barchat:
            if not orders_df.empty:
                st.bar_chart(orders_df, x="region", y="total_price")

        with region_barchart:
            if not orders_df.empty:
                st.bar_chart(orders_df, x="vendor", y="total_price")

        # Gráfico de vendas ao longo do tempo
        st.header("📈 Vendas por Data")
        if not orders_df.empty:
            orders_df = orders_df.sort_values(by="order_date")
            line_df = orders_df.groupby("order_date").sum().reset_index()
            st.line_chart(line_df, x="order_date", y="total_price")

        # Exibição detalhada dos pedidos
        st.header("📄 Detalhes dos Pedidos")
        if not orders_df.empty:
            st.dataframe(orders_df.iloc[::-1])

    # Atualiza o dashboard em tempo real
    st.rerun()
