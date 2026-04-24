from flask import Flask, request, Response
from flask_cors import CORS
import xml.etree.ElementTree as ET
import uuid

app = Flask(__name__)
CORS(app)

@app.route('/process_payment', methods=['POST'])
def pay():
    root = ET.fromstring(request.data)

    amount = float(root.find('Amount').text)
    product = root.find('ProductName').text
    qty = int(root.find('Quantity').text)

    res = ET.Element("PaymentResponse")

    if amount > 0:
        ET.SubElement(res, "Status").text = "Success"
        ET.SubElement(res, "TransactionID").text = f"TXN-{uuid.uuid4().hex[:8].upper()}"
        ET.SubElement(res, "Amount").text = str(amount)
        ET.SubElement(res, "ProductName").text = product
        ET.SubElement(res, "Quantity").text = str(qty)
    else:
        ET.SubElement(res, "Status").text = "Failed"

    return Response(ET.tostring(res, encoding="unicode"), mimetype="application/xml")


if __name__ == "__main__":
    app.run(port=5002, debug=True)