import streamlit as st
import sqlite3
import pandas as pd
from datetime import date

# Database setup
def init_db():
    conn = sqlite3.connect('mess.db')
    c = conn.cursor()
    # Add food_item column if not exists
    c.execute('''CREATE TABLE IF NOT EXISTS meals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL,
        student_name TEXT NOT NULL,
        meal_type TEXT NOT NULL,
        food_item TEXT,
        quantity INTEGER NOT NULL
    )''')
    # Try to add food_item column if missing (for old DBs)
    try:
        c.execute('ALTER TABLE meals ADD COLUMN food_item TEXT')
    except Exception:
        pass
    conn.commit()
    conn.close()


# Inject custom CSS for white background and black text
st.markdown('''
    <style>
    body, .stApp {
        background: #111 !important;
        color: #fff !important;
    }
    label, .stTextInput label, .stNumberInput label, .stSelectbox label, .stDateInput label, .stForm label, .st-bb, .st-c3, .st-c4, .st-c5, .st-c6, .st-c7, .st-c8, .st-c9, .st-ca, .st-cb, .st-cc, .st-cd, .st-ce, .st-cf, .st-cg, .st-ch, .st-ci, .st-cj, .st-ck, .st-cl, .st-cm, .st-cn, .st-co, .st-cp, .st-cq, .st-cr, .st-cs, .st-ct, .st-cu, .st-cv, .st-cw, .st-cx, .st-cy, .st-cz {
        color: #fff !important;
        font-size: 1.15rem !important;
    }
    input, select, textarea {
        color: #fff !important;
        background: #222 !important;
        font-size: 1.15rem !important;
    }
    .stDataFrame, .stTable, .stDataFrame table, .stTable table, .stDataFrame td, .stTable td, .stDataFrame th, .stTable th {
        font-size: 1.15rem !important;
        color: #fff !important;
        background: #222 !important;
    }
    /* Fix calendar visibility and font */
    .stDateInput input, .stDateInput label {
        font-size: 1.15rem !important;
        color: #fff !important;
        background: #222 !important;
    }
    .stDateInput [data-baseweb="datepicker"] {
        z-index: 9999 !important;
    }
    </style>
''', unsafe_allow_html=True)

init_db()

st.set_page_config(page_title="Mess Management System", layout="centered")
st.title("🍽️ Mess Management System")

# Sidebar for navigation

# Admin panel toggle
st.sidebar.markdown("---")
admin_mode = False
if st.sidebar.checkbox("Admin Panel"):
    admin_pass = st.sidebar.text_input("Enter admin password", type="password")
    if admin_pass == "admin123":
        admin_mode = True
        st.sidebar.success("Admin access granted!")
        # Admin Controls
        st.sidebar.markdown("### Admin Controls")
        conn = sqlite3.connect('mess.db')
        df_admin = pd.read_sql_query('SELECT id, date, student_name, meal_type, food_item, quantity FROM meals', conn)
        conn.close()
        if not df_admin.empty:
            del_id = st.sidebar.selectbox("Delete entry by ID", options=[None]+df_admin['id'].tolist(), key="admin_delete")
            if del_id:
                if st.sidebar.button(f"Delete Entry {del_id}", key="admin_delete_btn"):
                    conn = sqlite3.connect('mess.db')
                    c = conn.cursor()
                    c.execute('DELETE FROM meals WHERE id = ?', (del_id,))
                    conn.commit()
                    conn.close()
                    st.sidebar.success(f"Deleted entry with ID {del_id}")
                    st.rerun()
        else:
            st.sidebar.info("No entries to delete.")
    elif admin_pass:
        st.sidebar.error("Incorrect password")

section = st.sidebar.radio("Go to", ["Add Meal", "Analytics", "All Meals"])

# Add Meal Section
if section == "Add Meal":
    st.header("Add Meal Entry")
    with st.form("meal_form"):
        meal_date = st.date_input("Date", value=date.today())
        student_name = st.text_input("Student Name")
        meal_type = st.selectbox("Meal Type", ["Breakfast", "Lunch", "Dinner"])
        food_item = st.text_input("Food Item (e.g. Poha, Dal Rice, Paneer)")
        quantity = st.number_input("Quantity", min_value=1, value=1)
        submitted = st.form_submit_button("Add Meal")
        if submitted and student_name and food_item:
            conn = sqlite3.connect('mess.db')
            c = conn.cursor()
            c.execute('INSERT INTO meals (date, student_name, meal_type, food_item, quantity) VALUES (?, ?, ?, ?, ?)',
                      (meal_date.strftime('%Y-%m-%d'), student_name, meal_type, food_item, quantity))
            conn.commit()
            conn.close()
            st.success("Meal entry added!")

# Analytics Section
elif section == "Analytics":
    st.header("Analytics Dashboard")
    conn = sqlite3.connect('mess.db')
    df = pd.read_sql_query('SELECT * FROM meals', conn)
    conn.close()
    if df.empty:
        st.info("No meal data available.")
    else:
        total = df['quantity'].sum()
        most = df.groupby('meal_type')['quantity'].sum().idxmax()
        least = df.groupby('meal_type')['quantity'].sum().idxmin()
        st.markdown(f"**Total meals served:** {total}")
        st.markdown(f"**Most popular meal:** {most}")
        st.markdown(f"**Least popular meal:** {least}")
        st.bar_chart(df.groupby('meal_type')['quantity'].sum())

# All Meals Section
elif section == "All Meals":
    st.header("All Meals")
    conn = sqlite3.connect('mess.db')
    df = pd.read_sql_query('SELECT * FROM meals', conn)
    conn.close()
    if df.empty:
        st.info("No meal entries yet.")
    else:
        st.dataframe(df[['id','date','student_name','meal_type','food_item','quantity']])
        if admin_mode:
            # Delete option
            ids = df['id'].tolist()
            del_id = st.selectbox("Delete meal entry by ID", options=[None]+ids)
            if del_id:
                conn = sqlite3.connect('mess.db')
                c = conn.cursor()
                c.execute('DELETE FROM meals WHERE id = ?', (del_id,))
                conn.commit()
                conn.close()
                st.success(f"Deleted meal entry with ID {del_id}")
                st.rerun()
            # Download options
            st.download_button("Download as CSV", df.to_csv(index=False), file_name="meals.csv", mime="text/csv")
            import io
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, index=False)
            st.download_button(
                "Download as Excel",
                data=output.getvalue(),
                file_name="meals.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.info("Login to admin panel to delete or download data.")
