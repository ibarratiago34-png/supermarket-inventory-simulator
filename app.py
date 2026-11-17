import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Inventory Simulator", page_icon="📦", layout="wide")

if "language" not in st.session_state:
    st.session_state.language = "English"

lang = st.sidebar.radio("Language / Idioma", ["English", "Español"],
                        index=0 if st.session_state.language == "English" else 1)
st.session_state.language = lang
EN = lang == "English"

T = {
    "title": "Supermarket Inventory Management" if EN else "Gestión de inventario de supermercado",
    "subtitle": "Inventory planning and replenishment simulation" if EN else "Simulación de planificación y reposición de inventario",
    "settings": "Simulation settings" if EN else "Configuración de la simulación",
    "initial": "Initial stock (units)" if EN else "Stock inicial (unidades)",
    "demand": "Daily demand (units)" if EN else "Demanda diaria (unidades)",
    "reorder": "Reorder point (units)" if EN else "Punto de reposición (unidades)",
    "quantity": "Order quantity (units)" if EN else "Cantidad por pedido (unidades)",
    "delivery": "Delivery time (days)" if EN else "Tiempo de entrega (días)",
    "cost": "Unit cost ($)" if EN else "Costo por unidad ($)",
    "period": "Simulation period: 30 days" if EN else "Período de simulación: 30 días",
    "run": "Run simulation" if EN else "Ejecutar simulación",
    "scenarios": "Quick scenarios" if EN else "Escenarios rápidos",
    "baseline": "Baseline" if EN else "Situación inicial",
    "high": "High demand" if EN else "Alta demanda",
    "optimized": "Optimized" if EN else "Abastecimiento ajustado",
    "results": "Simulation results" if EN else "Resultados de la simulación",
    "final": "Final stock" if EN else "Stock final",
    "sales": "Total units sold" if EN else "Unidades vendidas",
    "lost": "Lost sales (units)" if EN else "Ventas perdidas (unidades)",
    "orders": "Total orders" if EN else "Pedidos realizados",
    "service": "Demand fulfillment" if EN else "Demanda satisfecha",
    "purchase": "Purchase value ($)" if EN else "Valor de compras ($)",
    "chart": "Daily inventory evolution" if EN else "Evolución diaria del inventario",
    "history": "Order history" if EN else "Historial de pedidos",
    "order_day": "Order day" if EN else "Día del pedido",
    "arrival": "Arrival day" if EN else "Día de llegada",
    "qty": "Quantity" if EN else "Cantidad",
    "no_orders": "No orders were placed." if EN else "No se realizaron pedidos.",
    "analysis": "Automatic analysis" if EN else "Análisis automático",
    "shortage": "Stock shortages occurred. Consider increasing the reorder point or order quantity, or reducing delivery time." if EN else "Se produjeron faltantes. Considerá aumentar el punto de reposición o la cantidad por pedido, o reducir el tiempo de entrega.",
    "ok": "All demand was fulfilled during the simulation." if EN else "Toda la demanda fue satisfecha durante la simulación.",
    "assumptions": "Model assumptions" if EN else "Supuestos del modelo",
    "a1": "Daily demand is constant." if EN else "La demanda diaria es constante.",
    "a2": "An order is placed when stock is at or below the reorder point." if EN else "Se realiza un pedido cuando el stock alcanza o queda por debajo del punto de reposición.",
    "a3": "Only one order can be outstanding at a time." if EN else "Solo puede haber un pedido pendiente a la vez.",
    "a4": "Unmet demand is treated as lost sales, not backorders." if EN else "La demanda insatisfecha se considera venta perdida y no pedido pendiente.",
    "a5": "Deliveries arrive at the beginning of the arrival day." if EN else "Las entregas llegan al comienzo del día de llegada.",
    "a6": "Purchase value is ordered quantity multiplied by unit cost; it is not total operating cost." if EN else "El valor de compras es la cantidad pedida multiplicada por el costo unitario; no representa el costo operativo total.",
}

st.title("📦 " + T["title"])
st.caption(T["subtitle"])
st.info("Product modeled: milk / Producto modelado: leche")

with st.sidebar:
    st.header(T["settings"])
    defaults = {"initial": 200, "demand": 25, "reorder": 60, "quantity": 100, "lead": 3, "cost": 1000.0}
    for key, value in defaults.items():
        if f"v_{key}" not in st.session_state:
            st.session_state[f"v_{key}"] = value
    initial = st.number_input(T["initial"], min_value=0, step=10, key="v_initial")
    demand = st.number_input(T["demand"], min_value=0, step=1, key="v_demand")
    reorder = st.number_input(T["reorder"], min_value=0, step=5, key="v_reorder")
    quantity = st.number_input(T["quantity"], min_value=1, step=10, key="v_quantity")
    lead_time = st.number_input(T["delivery"], min_value=1, step=1, key="v_lead")
    unit_cost = st.number_input(T["cost"], min_value=0.0, step=100.0, key="v_cost")

    st.divider()
    st.subheader(T["scenarios"])
    def load_preset(values):
        for k, v in values.items():
            st.session_state[f"v_{k}"] = v

    st.button(T["baseline"], use_container_width=True, on_click=load_preset,
              args=({"initial":200,"demand":25,"reorder":60,"quantity":100,"lead":3,"cost":1000.0},))
    st.button(T["high"], use_container_width=True, on_click=load_preset,
              args=({"initial":200,"demand":40,"reorder":60,"quantity":100,"lead":3,"cost":1000.0},))
    st.button(T["optimized"], use_container_width=True, on_click=load_preset,
              args=({"initial":200,"demand":25,"reorder":100,"quantity":150,"lead":2,"cost":1000.0},))

params = {
    "initial": int(initial), "demand": int(demand), "reorder": int(reorder),
    "quantity": int(quantity), "lead": int(lead_time), "cost": float(unit_cost)
}

def simulate(p):
    inventory = p["initial"]
    pending = None
    sales = lost = orders = ordered_units = 0
    stockout_days = 0
    rows, order_rows = [], []
    for day in range(1, 31):
        if pending is not None and pending["arrival"] == day:
            inventory += pending["quantity"]
            pending = None

        sold = min(inventory, p["demand"])
        shortage = p["demand"] - sold
        inventory -= sold
        sales += sold
        lost += shortage
        if shortage > 0:
            stockout_days += 1

        if inventory <= p["reorder"] and pending is None:
            orders += 1
            ordered_units += p["quantity"]
            pending = {"arrival": day + p["lead"], "quantity": p["quantity"]}
            order_rows.append({
                T["order_day"]: day,
                T["arrival"]: day + p["lead"],
                T["qty"]: p["quantity"]
            })

        rows.append({"Day / Día": day, "Inventory / Inventario": inventory,
                     "Reorder point / Punto de reposición": p["reorder"]})

    total_demand = p["demand"] * 30
    fulfillment = (sales / total_demand * 100) if total_demand else 100.0
    return {
        "final": inventory, "sales": sales, "lost": lost, "orders": orders,
        "ordered": ordered_units, "stockout_days": stockout_days,
        "fulfillment": fulfillment, "purchase_value": ordered_units * p["cost"],
        "rows": rows, "order_rows": order_rows, "total_demand": total_demand
    }

if st.button(T["run"], type="primary", use_container_width=True):
    st.session_state.result = simulate(params)
    st.session_state.last_params = params

if "result" in st.session_state:
    r = st.session_state.result
    st.header(T["results"])
    c1, c2, c3 = st.columns(3)
    c1.metric(T["final"], f'{r["final"]:,}')
    c2.metric(T["sales"], f'{r["sales"]:,}')
    c3.metric(T["lost"], f'{r["lost"]:,}')
    c4, c5, c6 = st.columns(3)
    c4.metric(T["orders"], f'{r["orders"]:,}')
    c5.metric(T["service"], f'{r["fulfillment"]:.1f}%')
    c6.metric(T["purchase"], f'$ {r["purchase_value"]:,.2f}')

    df = pd.DataFrame(r["rows"])
    st.subheader(T["chart"])
    fig = px.line(df, x="Day / Día", y=["Inventory / Inventario",
                                       "Reorder point / Punto de reposición"],
                  markers=True)
    fig.update_layout(xaxis_title="Day / Día", yaxis_title="Units / Unidades",
                      legend_title="")
    st.plotly_chart(fig, use_container_width=True)

    st.subheader(T["history"])
    if r["order_rows"]:
        st.dataframe(pd.DataFrame(r["order_rows"]), use_container_width=True, hide_index=True)
    else:
        st.write(T["no_orders"])

    st.subheader(T["analysis"])
    if r["lost"] > 0:
        st.warning(T["shortage"])
    else:
        st.success(T["ok"])
    st.caption(
        (f'Total demand / Demanda total: {r["total_demand"]} · '
         f'Stockout days / Días con faltantes: {r["stockout_days"]} · '
         f'Units ordered / Unidades pedidas: {r["ordered"]}')
    )

    export = pd.DataFrame(r["rows"])
    st.download_button(
        "Download daily results / Descargar resultados diarios",
        data=export.to_csv(index=False).encode("utf-8"),
        file_name="inventory_simulation_results.csv",
        mime="text/csv"
    )
else:
    st.info(T["run"] + " — " + ("to see the results." if EN else "para ver los resultados."))

with st.expander(T["assumptions"]):
    for key in ["a1", "a2", "a3", "a4", "a5", "a6"]:
        st.write("• " + T[key])
