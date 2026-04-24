from flask import Flask, request, Response, render_template
from flask_cors import CORS
import xml.etree.ElementTree as ET
import uuid
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)

# =========================
# FILES
# =========================
INVENTORY_FILE = "inventory.xml"
ORDERS_FILE = "orders.xml"
RECEIPTS_FILE = "receipts.xml"


# =========================
# HELPERS
# =========================
def load_xml(file):
    if os.path.exists(file):
        try:
            return ET.parse(file).getroot()
        except:
            pass
    return ET.Element("Root")


def save_xml(file, root):
    ET.ElementTree(root).write(file, encoding="unicode", xml_declaration=True)


# =========================
# INVENTORY
# =========================
@app.route("/inventory", methods=["GET"])
def inventory():
    root = load_xml(INVENTORY_FILE)
    return Response(ET.tostring(root, encoding="unicode"), mimetype="application/xml")


def process_inventory(code, qty):
    root = load_xml(INVENTORY_FILE)

    for item in root.findall("Item"):
        if item.find("Code").text == code:
            stock = int(item.find("Stock").text)

            if stock < qty:
                res = ET.Element("Response")
                ET.SubElement(res, "Status").text = "Failed"
                ET.SubElement(res, "Message").text = "Not enough stock"
                return None, res

            new_stock = stock - qty
            item.find("Stock").text = str(new_stock)
            save_xml(INVENTORY_FILE, root)

            res = ET.Element("Response")
            ET.SubElement(res, "Status").text = "Success"
            ET.SubElement(res, "Name").text = item.find("Name").text
            ET.SubElement(res, "Brand").text = item.find("Brand").text
            ET.SubElement(res, "Price").text = item.find("Price").text
            ET.SubElement(res, "RemainingStock").text = str(new_stock)

            return item, res

    res = ET.Element("Response")
    ET.SubElement(res, "Status").text = "Failed"
    ET.SubElement(res, "Message").text = "Item not found"
    return None, res


# =========================
# PAYMENT
# =========================
def process_payment(amount, product, qty):
    res = ET.Element("PaymentResponse")

    if amount > 0:
        ET.SubElement(res, "Status").text = "Success"
        ET.SubElement(res, "TransactionID").text = f"TXN-{uuid.uuid4().hex[:8].upper()}"
        ET.SubElement(res, "Amount").text = str(amount)
        ET.SubElement(res, "ProductName").text = product
        ET.SubElement(res, "Quantity").text = str(qty)
    else:
        ET.SubElement(res, "Status").text = "Failed"

    return res


# =========================
# ORDER PLACE
# =========================
@app.route("/place_order", methods=["POST"])
def place_order():
    root = ET.fromstring(request.data)

    code = root.find("ProductCode").text
    qty = int(root.find("Quantity").text)
    cname = root.find("CustomerName").text if root.find("CustomerName") is not None else "Guest"

    # STEP 1: INVENTORY
    item, inv_res = process_inventory(code, qty)
    if item is None:
        return Response(ET.tostring(inv_res, encoding="unicode"), mimetype="application/xml")

    pname = item.find("Name").text
    brand = item.find("Brand").text
    price = float(item.find("Price").text)
    total = price * qty

    # STEP 2: PAYMENT
    pay_res = process_payment(total, pname, qty)
    if pay_res.find("Status").text != "Success":
        return Response(ET.tostring(pay_res, encoding="unicode"), mimetype="application/xml")

    txn = pay_res.find("TransactionID").text

    # STEP 3: SAVE ORDER
    orders = load_xml(ORDERS_FILE)
    o = ET.SubElement(orders, "Order")

    ET.SubElement(o, "TransactionID").text = txn
    ET.SubElement(o, "CustomerName").text = cname
    ET.SubElement(o, "ProductCode").text = code
    ET.SubElement(o, "ProductName").text = pname
    ET.SubElement(o, "Brand").text = brand
    ET.SubElement(o, "Quantity").text = str(qty)
    ET.SubElement(o, "TotalAmount").text = str(total)
    ET.SubElement(o, "Timestamp").text = datetime.now().strftime("%Y-%m-%d %H:%M")

    save_xml(ORDERS_FILE, orders)

    # STEP 4: SAVE RECEIPT
    receipts = load_xml(RECEIPTS_FILE)
    r = ET.SubElement(receipts, "Receipt")

    ET.SubElement(r, "TransactionID").text = txn
    ET.SubElement(r, "CustomerName").text = cname
    ET.SubElement(r, "ProductName").text = pname
    ET.SubElement(r, "Brand").text = brand
    ET.SubElement(r, "Quantity").text = str(qty)
    ET.SubElement(r, "PricePerUnit").text = str(price)
    ET.SubElement(r, "TotalAmount").text = str(total)
    ET.SubElement(r, "Timestamp").text = datetime.now().strftime("%Y-%m-%d %H:%M")

    save_xml(RECEIPTS_FILE, receipts)

    # RESPONSE
    res = ET.Element("OrderResponse")
    ET.SubElement(res, "Status").text = "Success"
    ET.SubElement(res, "TransactionID").text = txn
    ET.SubElement(res, "CustomerName").text = cname
    ET.SubElement(res, "ProductName").text = pname
    ET.SubElement(res, "Brand").text = brand
    ET.SubElement(res, "Quantity").text = str(qty)
    ET.SubElement(res, "TotalAmount").text = str(total)

    return Response(ET.tostring(res, encoding="unicode"), mimetype="application/xml")


# =========================
# HISTORY
# =========================
@app.route("/order_history")
def history():
    return Response(
        ET.tostring(load_xml(ORDERS_FILE), encoding="unicode"),
        mimetype="application/xml"
    )


@app.route("/receipts")
def receipts():
    return Response(
        ET.tostring(load_xml(RECEIPTS_FILE), encoding="unicode"),
        mimetype="application/xml"
    )


# =========================
# FRONTEND
# =========================
@app.route("/")
def home():
    return render_template("index.html")


# =========================
# RUN (RENDER READY)
# =========================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))