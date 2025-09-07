import streamlit as st
import sqlite3
import pandas as pd
from datetime import date

# Database setup
def init_db():
    conn = sqlite3.connect('mess.db')
    c = conn.cursor()
    # Add phone_number and food_item columns if not exists
    c.execute('''CREATE TABLE IF NOT EXISTS meals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL,
        student_name TEXT NOT NULL,
        phone_number TEXT NOT NULL,
        meal_type TEXT NOT NULL,
        food_item TEXT,
        quantity INTEGER NOT NULL
    )''')
    # Try to add columns if missing (for old DBs)
    try:
        c.execute('ALTER TABLE meals ADD COLUMN food_item TEXT')
    except Exception:
        pass
    try:
        c.execute('ALTER TABLE meals ADD COLUMN phone_number TEXT NOT NULL DEFAULT ""')
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
        text-shadow: 0 1px 2px #000, 0 0px 1px #222;
    }
    input, select, textarea {
        color: #fff !important;
        background: #222 !important;
        font-size: 1.15rem !important;
        text-shadow: 0 1px 2px #000, 0 0px 1px #222;
    }
    button, .stButton > button {
        color: #fff !important;
        background: #0078d4 !important;
        font-weight: bold !important;
        text-shadow: 0 1px 2px #000, 0 0px 1px #222;
        border-radius: 6px !important;
        border: none !important;
        letter-spacing: 0.5px;
        font-size: 1.15rem !important;
    }
    select, option {
        color: #fff !important;
        background: #222 !important;
        font-size: 1.15rem !important;
        text-shadow: 0 1px 2px #000, 0 0px 1px #222;
        font-weight: bold !important;
        letter-spacing: 0.5px;
        text-transform: uppercase;
    }
    @media (max-width: 600px) {
        body, .stApp, label, input, select, textarea, .stDataFrame, .stTable, .stDataFrame table, .stTable table, .stDataFrame td, .stTable td, .stDataFrame th, .stTable th {
            font-size: 1.05rem !important;
        }
        .stDataFrame, .stTable {
            font-size: 0.95rem !important;
        }
    }
    .stDataFrame, .stTable, .stDataFrame table, .stTable table, .stDataFrame td, .stTable td, .stDataFrame th, .stTable th {
        font-size: 1.15rem !important;
        color: #fff !important;
        background: #222 !important;
        text-shadow: 0 1px 2px #000, 0 0px 1px #222;
    }
    /* Fix calendar visibility and font */
    .stDateInput input, .stDateInput label {
        font-size: 1.15rem !important;
        color: #fff !important;
        background: #222 !important;
        text-shadow: 0 1px 2px #000, 0 0px 1px #222;
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
    st.header("Add Meal Entry (Add to Cart, max 5 items)")
    # Use session state for cart
    if 'cart' not in st.session_state:
        st.session_state.cart = []
    with st.form("meal_cart_form"):
        meal_date = st.date_input("Date", value=date.today())
        student_name = st.text_input("Student Name")
        phone_number = st.text_input("Phone Number (required)")
        meal_type = st.selectbox("Meal Type", ["Breakfast", "Lunch", "Dinner"])
        # Get all food items already used for this date
        conn = sqlite3.connect('mess.db')
        c = conn.cursor()
        c.execute('SELECT food_item, meal_type FROM meals WHERE date = ?', (meal_date.strftime('%Y-%m-%d'),))
        used_items = c.fetchall()
        conn.close()
        # Only show a blank text input for food item
        food_item = st.text_input("Food Item", key=f"food_item_{meal_type}_{meal_date}").strip()
        quantity = st.number_input("Quantity", min_value=1, value=1)
        add_to_cart = st.form_submit_button("Add to Cart")
        # Allow duplicate food items only for Lunch and Dinner, not for Breakfast
        if meal_type == "Breakfast":
            duplicate = food_item and any((food_item.lower() == item.lower() and mtype != meal_type) for item, mtype in used_items)
            cart_duplicate = food_item and any((food_item.lower() == item['food_item'].lower() and item['meal_type'] != meal_type) for item in st.session_state.cart)
        else:
            duplicate = False
            cart_duplicate = False
        if add_to_cart and student_name and phone_number and food_item:
            if duplicate or cart_duplicate:
                st.error(f'Not possible to make "{food_item}" for {meal_type} because it is already used for another meal type on this date or in your cart!')
            elif len(st.session_state.cart) >= 5:
                st.error("You can only add up to 5 items to the cart.")
            else:
                st.session_state.cart.append({
                    'date': meal_date.strftime('%Y-%m-%d'),
                    'student_name': student_name,
                    'phone_number': phone_number,
                    'meal_type': meal_type,
                    'food_item': food_item,
                    'quantity': quantity
                })
                st.success(f'Added "{food_item}" to cart!')
    # Show cart
    if st.session_state.cart:
        st.subheader("Cart")
        for i, item in enumerate(st.session_state.cart):
            st.write(f"{i+1}. {item['meal_type']} | {item['food_item']} | Qty: {item['quantity']} | {item['student_name']} | {item['phone_number']}")
        if st.button("Submit Order (Add All)"):
            conn = sqlite3.connect('mess.db')
            c = conn.cursor()
            for item in st.session_state.cart:
                c.execute('INSERT INTO meals (date, student_name, phone_number, meal_type, food_item, quantity) VALUES (?, ?, ?, ?, ?, ?)',
                          (item['date'], item['student_name'], item['phone_number'], item['meal_type'], item['food_item'], item['quantity']))
            conn.commit()
            conn.close()
            st.success("All items in cart added!")
            st.session_state.cart = []
            st.rerun()
        if st.button("Clear Cart"):
            st.session_state.cart = []
            st.rerun()

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
        st.dataframe(df[['id','date','student_name','phone_number','meal_type','food_item','quantity']])
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
