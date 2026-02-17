import requests
import random

# Configuration
BASE_URL = "http://localhost:8000/api"
NUM_ORDERS = 50  # increase load

TOTAL_STORES = 25  # we KNOW this
TOTAL_PRODUCTS = 1200  # informational
TOTAL_INVENTORY = 7000  # informational


def get_store_inventory(store_id):
    url = f"{BASE_URL}/stores/{store_id}/inventory/"
    print(f"Calling: {url}")
    response = requests.get(url)
    print("Status:", response.status_code)
    print("Response:", response.text)
    response.raise_for_status()
    data = response.json()
    return data["results"]



def create_order(store_id, items):
    """Create an order"""
    response = requests.post(
        f"{BASE_URL}/orders/",
        json={
            "store_id": store_id,
            "items": items
        }
    )
    return response


def main():
    print(f"📦 Creating {NUM_ORDERS} random orders...")
    print(f"🏬 Total Stores: {TOTAL_STORES}")
    print(f"🛒 Total Products: {TOTAL_PRODUCTS}")
    print(f"📊 Total Inventory Records: {TOTAL_INVENTORY}\n")

    successful = 0
    failed = 0

    for i in range(NUM_ORDERS):

        # 🔥 Pick random store using known ID range
        store_id = random.randint(1, TOTAL_STORES)

        # Get inventory for this store
        inventory_data = get_store_inventory(store_id)

        # Filter products with stock > 5
        in_stock_products = [
            item for item in inventory_data
            if item["quantity"] > 5
        ]

        if len(in_stock_products) < 2:
            print(f"⚠️ Store {store_id} doesn't have enough stock, skipping")
            continue

        # Pick 2-4 random products
        num_items = random.randint(2, 4)
        selected = random.sample(
            in_stock_products,
            min(num_items, len(in_stock_products))
        )

        items = []

        for product in selected:
            max_safe_qty = max(1, product["quantity"] // 2)
            qty = random.randint(1, min(5, max_safe_qty))

            product_id = product.get("product_id") or product.get("id")

            items.append({
                "product_id": product_id,
                "quantity_requested": qty
            })

        # Create order
        response = create_order(store_id, items)

        if response.status_code == 201:
            order_data = response.json()
            print(
                f"✅ Order #{order_data['id']} | "
                f"Store {store_id} | "
                f"{len(items)} items | "
                f"{order_data['status']}"
            )
            successful += 1
        else:
            print(f"❌ Failed (Store {store_id}): {response.status_code}")
            failed += 1

    print("\n🎯 FINAL SUMMARY")
    print(f"✅ Successful: {successful}")
    print(f"❌ Failed: {failed}")


if __name__ == "__main__":
    main()
