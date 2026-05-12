import streamlit as st
import pandas as pd
import sqlite3
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from sklearn.model_selection import train_test_split
from datetime import timedelta
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import LabelEncoder

st.set_page_config(page_title="Superstore Dashboard",layout="wide")

if "user" not in st.session_state:
    st.session_state["user"] = ""

if st.session_state["user"] == "":
    st.title("Login")
    username = st.text_input("Enter Name")
    if st.button("Login"):
        if username:
            st.session_state["user"] = username
            st.rerun()
        else:
            st.warning("Enter your name")
    st.stop()

st.title("📊 Superstore Data Dashboard")
st.write(f"Welcome {st.session_state['user']}")
if st.button("Logout"):
    st.session_state["user"] = ""
    st.rerun()

file = st.file_uploader("Upload CSV / Excel",type=["csv", "xlsx"])
if file:

    if file.name.endswith(".csv"):
        df = pd.read_csv(file)
    else:
        df = pd.read_excel(file)

    st.subheader("📄 Raw Data")
    st.dataframe(df, use_container_width=True)

    st.subheader("🔍 Data Quality Check")

    c1, c2, c3 = st.columns(3)
    c1.metric("Rows", df.shape[0])
    c2.metric("Columns", df.shape[1])
    c3.metric("Duplicates", df.duplicated().sum())
    st.write("Null Values")
    st.write(df.isnull().sum())

    if st.checkbox("Remove Duplicates"):
        df = df.drop_duplicates()
        st.success("Duplicates Removed")

    st.subheader("🧹 Handle Null Values")

    method = st.selectbox("Select Method",["None","Mean (Average)","Median (Middle Value)","Mode (Most Repeated)"],
        key="null_method")

    if method == "Mean (Average)":
        df = df.fillna(df.mean(numeric_only=True))
    elif method == "Median (Middle Value)":
        df = df.fillna(df.median(numeric_only=True) )
    elif method == "Mode (Most Repeated)":
        df = df.fillna(
            df.mode().iloc[0])

    st.subheader("✅ Cleaned Data")
    st.dataframe(df, use_container_width=True)

    st.subheader("🔽 Filter Data")
    filter_df = df.copy()

    if "Ship_Mode" in df.columns:

        ship = st.multiselect("Ship Mode",df["Ship_Mode"].dropna().unique(),key="ship_filter")
        if ship:
            filter_df = filter_df[filter_df["Ship_Mode"].isin(ship)]

    if "Region" in df.columns:

        region = st.multiselect("Region",df["Region"].dropna().unique(),key="region_filter")
        if region:
            filter_df = filter_df[filter_df["Region"].isin(region)]

    if "Category" in df.columns:

        category = st.multiselect("Category",df["Category"].dropna().unique(),key="category_filter")
        if category:
            filter_df = filter_df[filter_df["Category"].isin(category)]

    if "Sub_Category" in df.columns:

        subcat = st.multiselect("Sub Category",df["Sub_Category"].dropna().unique(),key="subcat_filter")
        if subcat:
            filter_df = filter_df[filter_df["Sub_Category"].isin(subcat)]
    df = filter_df

    st.subheader("📌 Key Metrics")

    m1, m2, m3 = st.columns(3)

    sales = df["Sales"].sum() if "Sales" in df.columns else 0
    quantity = df["Quantity"].sum() if "Quantity" in df.columns else 0
    profit = df["Profit"].sum() if "Profit" in df.columns else 0

    m1.metric("Total Sales", round(sales, 2))
    m2.metric("Total Quantity", int(quantity))
    m3.metric("Total Profit", round(profit, 2))

    if "Sales" in df.columns:

        avg_sales = df["Sales"].mean()

        df["Sales_Level"] = df["Sales"].apply(
            lambda x: "High"
            if x > avg_sales
            else "Low")

    st.subheader("💾 Save to SQLite")

    if st.button("Save to SQLite"):

        conn = sqlite3.connect("sales_data.db")
        table_name = file.name.split(".")[0]
        table_name = table_name.replace(" ", "_")
        df.to_sql(table_name,conn,if_exists="replace",index=False)
        conn.close()

        st.success(f"Saved as table: {table_name}")

    st.subheader("🗄️ SQLite Dashboard")

    if st.button("Load DB Tables"):
        conn = sqlite3.connect("sales_data.db")
        tables = pd.read_sql("SELECT name FROM sqlite_master WHERE type='table';",conn)

        if tables.empty:
         st.warning("No Tables Found")
        else:
            st.write(tables)
            table = st.selectbox("Select Table",tables["name"],key="db_table")

            db_df = pd.read_sql(f"SELECT * FROM {table}",conn)
            st.dataframe(db_df,use_container_width=True)
        conn.close()


    st.subheader("Secure Download Database")

    download_user = st.text_input("Enter Username")
    download_pass = st.text_input("Enter Password", type="password")

    allowed_users = {"Nirai": "12345","admin": "67890"}

    if download_user and download_pass:
        if download_user in allowed_users and allowed_users[download_user] == download_pass:

            with open("sales_data.db", "rb") as file:
                st.download_button(label="Download SQLite DB",
                                   data=file,
                                   file_name="secure_database.db",
                                   mime="application/octet-stream")
            st.success("Access granted. You can download the database.")
        else:
            st.error("Invalid username or password.")

    st.subheader("📊 Visualization")

    num_cols = df.select_dtypes(include=["int64", "float64"]).columns
    cat_cols = df.select_dtypes(include="object").columns

    if len(num_cols) > 0 and len(cat_cols) > 0:

        chart = st.selectbox("Select Chart",["Bar", "Line", "Pie"],key="chart_type")

        x = st.selectbox("Category",cat_cols,key="x_axis")
        y = st.selectbox("Value",num_cols,key="y_axis")
        grouped = df.groupby(x)[y].sum().reset_index()
        fig, ax = plt.subplots()

        if chart == "Bar":
            sns.barplot(data=grouped,x=x,y=y,ax=ax)
        elif chart == "Line":
            sns.lineplot(data=grouped,x=x,y=y,ax=ax)
        elif chart == "Pie":
            ax.pie(grouped[y],labels=grouped[x],autopct="%1.1f%%")
        st.pyplot(fig)

st.title("Sales Production Prediction Dashboard")

data = {"Date": pd.date_range(start="2025-01-01", periods=500),
        "Category": np.random.choice(["Furniture", "Technology", "Office Supplies"],500),
        "Sub_Category": np.random.choice(["Bookcases","Chairs","Labels","Tables","Storage","Furnishings","Art","Phones","Binders","Appliances","Paper"],500),
        "Region": np.random.choice(["South", "West", "Central"],500),
        "Ship_Mode": np.random.choice(["Second Class", "Standard Class"],500),
        "Sales": np.random.randint(1000, 10000, 500)}
df = pd.DataFrame(data)

df["Day"] = df["Date"].dt.day
df["Week"] = df["Date"].dt.isocalendar().week.astype(int)
df["Month"] = df["Date"].dt.month
df["Year"] = df["Date"].dt.year

le_category = LabelEncoder()
le_sub = LabelEncoder()
le_region = LabelEncoder()
le_ship = LabelEncoder()

df["Category"] = le_category.fit_transform(df["Category"])
df["Sub_Category"] = le_sub.fit_transform(df["Sub_Category"])
df["Region"] = le_region.fit_transform(df["Region"])
df["Ship_Mode"] = le_ship.fit_transform(df["Ship_Mode"])

X = df[["Day","Week","Month","Year","Category","Sub_Category","Region","Ship_Mode"]]
y = df["Sales"]

X_train, X_test, y_train, y_test = train_test_split(X,y,test_size=0.2,random_state=42)
model = RandomForestRegressor(n_estimators=100,random_state=42)
model.fit(X_train, y_train)

st.sidebar.header("Prediction Inputs")
prediction_type = st.sidebar.selectbox("Prediction Type",["Day", "Week", "Month", "Year"])

day = 1
week = 1
month = 1
year = 2025
category = st.sidebar.selectbox("Category",le_category.classes_)
sub_category = st.sidebar.selectbox("Sub Category",le_sub.classes_)
region = st.sidebar.selectbox("Region",le_region.classes_)
ship_mode = st.sidebar.selectbox("Ship Mode",le_ship.classes_)

category_encoded = le_category.transform([category])[0]
sub_encoded = le_sub.transform([sub_category])[0]
region_encoded = le_region.transform([region])[0]
ship_encoded = le_ship.transform([ship_mode])[0]

input_data = pd.DataFrame({"Day": [day],"Week": [week],"Month": [month],"Year": [year],"Category": [category_encoded],"Sub_Category": [sub_encoded],"Region": [region_encoded],"Ship_Mode": [ship_encoded]})
prediction = model.predict(input_data)[0]

st.subheader("Predicted Sales")

st.success(f"""

Prediction Type : {prediction_type}

Category : {category}

Sub Category : {sub_category}

Region : {region}

Ship Mode : {ship_mode}

Predicted Sales : ₹ {prediction:,.2f}

""")

average_sales = df["Sales"].mean()
if prediction > average_sales:
    st.info("Production/Sales will be HIGH")
else:
    st.warning("Production/Sales will be LOW")

st.subheader(f"{prediction_type} Sales Prediction Graph")
x_values = []
future_predictions = []

if prediction_type == "Day":
    x_values = list(range(1, 31))
    for d in x_values:

        temp = pd.DataFrame({
            "Day": [d],
            "Week": [week],
            "Month": [month],
            "Year": [year],
            "Category": [category_encoded],
            "Sub_Category": [sub_encoded],
            "Region": [region_encoded],
            "Ship_Mode": [ship_encoded]})

        pred = model.predict(temp)[0]
        future_predictions.append(pred)
    x_label = "Days"
elif prediction_type == "Week":

    x_values = list(range(1, 53))

    for w in x_values:
        temp = pd.DataFrame({
            "Day": [day],
            "Week": [w],
            "Month": [month],
            "Year": [year],
            "Category": [category_encoded],
            "Sub_Category": [sub_encoded],
            "Region": [region_encoded],
            "Ship_Mode": [ship_encoded]})

        pred = model.predict(temp)[0]
        future_predictions.append(pred)
    x_label = "Weeks"
elif prediction_type == "Month":
    x_values = list(range(1, 13))
    for m in x_values:
        temp = pd.DataFrame({
            "Day": [day],
            "Week": [week],
            "Month": [m],
            "Year": [year],
            "Category": [category_encoded],
            "Sub_Category": [sub_encoded],
            "Region": [region_encoded],
            "Ship_Mode": [ship_encoded]})

        pred = model.predict(temp)[0]
        future_predictions.append(pred)

    x_label = "Months"
elif prediction_type == "Year":
    x_values = list(range(2025, 2031))
    for y in x_values:
        temp = pd.DataFrame({
            "Day": [day],
            "Week": [week],
            "Month": [month],
            "Year": [y],
            "Category": [category_encoded],
            "Sub_Category": [sub_encoded],
            "Region": [region_encoded],
            "Ship_Mode": [ship_encoded]})

        pred = model.predict(temp)[0]
        future_predictions.append(pred)
    x_label = "Years"
fig, ax = plt.subplots(figsize=(10, 5))
ax.plot(x_values,future_predictions,marker="o")
ax.set_xlabel(x_label)
ax.set_ylabel("Predicted Sales")
ax.set_title(f"{prediction_type} Wise Sales Prediction")
st.pyplot(fig)

st.subheader(f"{prediction_type} Wise Prediction Table")
table_df = pd.DataFrame({
    prediction_type: x_values,
    "Predicted Sales": np.round(future_predictions, 2)})
st.dataframe(table_df)

csv = table_df.to_csv(index=False).encode("utf-8")

st.download_button(label="Download Prediction CSV",
                   data=csv,
                   file_name="sales_prediction.csv",
                   mime="text/csv")

st.markdown("""
<style>
div.stButton > button {
    background-color: red;
    color: white;
    width: 100%;}
</style>
""", unsafe_allow_html=True)
col1, col2, col3 = st.columns([1,1,1])
with col2:
    if st.button("Logout", key="logout_btn_1"):
        st.session_state.clear()
        st.rerun()
