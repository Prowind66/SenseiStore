import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta

# Load product data
product_df = pd.read_csv("drinks_content_edited.csv", encoding="unicode_escape")

# Clean price columns
product_df['product_original_price'] = (
    product_df['product_original_price']
    .astype(str)
    .str.replace('$', '', regex=False)
    .str.replace(',', '', regex=False)
    .str.strip()
    .replace('', np.nan)
    .astype(float)
)

product_df['product_discounted_price'] = (
    product_df['product_discounted_price']
    .astype(str)
    .str.replace('$', '', regex=False)
    .str.replace(',', '', regex=False)
    .str.strip()
    .replace('', '0')
    .astype(float)
)

# Filter rows with valid essential fields
product_df = product_df[
    (product_df['product_original_price'].notnull()) &
    (product_df['product_category'].notnull()) &
    (product_df['product_name'].notnull())
]

# Generate synthetic orders
num_orders = 3000
order_ids = [f"ORD{1000 + i}" for i in range(num_orders)]
customer_ids = [f"CUST{random.randint(1, 500)}" for _ in range(num_orders)]
customer_types = [random.choice(['B2B', 'B2C']) for _ in range(num_orders)]
order_dates = [datetime(2023, 1, 1) + timedelta(days=random.randint(0, 364)) for _ in range(num_orders)]

orders = []

for i in range(num_orders):
    row = product_df.sample(1).iloc[0]
    product = row['product_name']
    category = row['product_category']
    original_price = row['product_original_price']
    discounted_price = row['product_discounted_price']
    quantity = random.randint(1, 100)
    product_image_url = row["product_image"]
    product_bottle_type = row["product_bottle_type"]
    product_dietary_attribute = row["product_dietary_attribute"]
    product_company = row["product_company"]

    total_price = 0
    # Simple rule: if discounted_price exists, use it directly
    if discounted_price > 0:
        unit_price = original_price
        discount = discounted_price  # No extra calculation needed
        total_price = round(discount * quantity, 2)
    else:
        unit_price = original_price
        discount = 0
        total_price = round(unit_price * quantity, 2)

    orders.append({
        "Order_ID": order_ids[i],
        "Customer_ID": customer_ids[i],
        "Customer_Type": customer_types[i],
        "Product": product,
        "Category": category,
        "Unit_Price": round(unit_price, 2),
        "Quantity": quantity,
        "Discount": discount,
        "Total_Price": total_price,
        "Order_Date": order_dates[i].strftime('%d/%m/%Y'),
        "Product_Image_Url" : product_image_url,
        "Product_Bottle_Type" : product_bottle_type,
        "Product_Dietary_Attribute" : product_dietary_attribute,
        "Product_Company" : product_company
    })

# Create DataFrame
sales_df = pd.DataFrame(orders)

# Set data types
sales_df = sales_df.astype({
    "Order_ID": "string",
    "Customer_ID": "string",
    "Customer_Type": "category",
    "Product": "string",
    "Category": "category",
    "Unit_Price": "float",
    "Quantity": "int",
    "Discount": "float",
    "Total_Price": "float",
    "Order_Date": "string",
    "Product_Image_Url" : "string",
    "Product_Bottle_Type" : "string",
    "Product_Dietary_Attribute" : "string",
    "Product_Company" : "string"
})

# Save to CSV
sales_df.to_csv("synthetic_sales_data.csv", index=False, encoding="utf-8-sig")
print("✅ Synthetic sales data saved as 'synthetic_sales_data.csv'")
