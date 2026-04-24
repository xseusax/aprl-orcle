from flask import Flask, Response, request
from flask_cors import CORS
import xml.etree.ElementTree as ET

app = Flask(__name__)
CORS(app)

FILE = "inventory.xml"

def load():
    return ET.parse(FILE).getroot()

@app.route("/inventory", methods=["GET"])
def inventory():
    root = load()
    return Response(ET.tostring(root, encoding="unicode"), mimetype="application/xml")


@app.route("/update_inventory", methods=["POST"])
def update():
    root = load()
    req = ET.fromstring(request.data)

    code = req.find("ProductCode").text
    qty = int(req.find("Quantity").text)

    for item in root.findall("Item"):
        if item.find("Code").text == code:
            stock = int(item.find("Stock").text)

            if stock < qty:
                return Response("""
                <Response>
                    <Status>Failed</Status>
                    <Message>Not enough stock</Message>
                </Response>
                """, mimetype="application/xml")

            item.find("Stock").text = str(stock - qty)

            ET.ElementTree(root).write(FILE, encoding="unicode")

            return Response(f"""
            <Response>
                <Status>Success</Status>
                <Name>{item.find('Name').text}</Name>
                <Brand>{item.find('Brand').text}</Brand>
                <Price>{item.find('Price').text}</Price>
                <RemainingStock>{stock - qty}</RemainingStock>
            </Response>
            """, mimetype="application/xml")

    return Response("""
    <Response>
        <Status>Failed</Status>
        <Message>Item not found</Message>
    </Response>
    """, mimetype="application/xml")


if __name__ == "__main__":
    app.run(port=5001, debug=True)