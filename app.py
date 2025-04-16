from flask import Flask, render_template, request, redirect, url_for
import pickle
import os

app = Flask(__name__)

class ZestyZomato:
    def __init__(self):
        self.menu = {}
        self.orders = {}
        self.order_id_counter = 1
        self.coupons = {"SAVE10": 10, "SAVE20": 20}
        self.load_data()

    def save_data(self):
        with open("zomato.pkl", "wb") as f:
            pickle.dump((self.menu, self.orders, self.order_id_counter), f)

    def load_data(self):
        if os.path.exists("zomato.pkl"):
            with open("zomato.pkl", "rb") as f:
                self.menu, self.orders, self.order_id_counter = pickle.load(f)

zomato = ZestyZomato()

@app.route('/')
def home():
    return render_template("index.html")

@app.route('/menu')
def view_menu():
    return render_template("menu.html", menu=zomato.menu)

@app.route('/add_dish', methods=["GET", "POST"])
def add_dish():
    if request.method == "POST":
        dish_id = request.form["dish_id"]
        name = request.form["name"]
        price = float(request.form["price"])
        available = request.form.get("available") == "on"
        zomato.menu[dish_id] = {"name": name, "price": price, "available": available}
        zomato.save_data()
        return redirect(url_for("view_menu"))
    return render_template("add_dish.html")

@app.route('/remove_dish/<dish_id>')
def remove_dish(dish_id):
    zomato.menu.pop(dish_id, None)
    zomato.save_data()
    return redirect(url_for("view_menu"))

@app.route('/take_order', methods=["GET", "POST"])
def take_order():
    if request.method == "POST":
        customer_name = request.form["customer_name"]
        dish_ids = request.form.getlist("dish_ids")
        coupon_code = request.form["coupon_code"].strip().upper()

        total_price = 0
        ordered_dishes = {}
        for dish_id in dish_ids:
            if dish_id in zomato.menu and zomato.menu[dish_id]["available"]:
                ordered_dishes[dish_id] = zomato.menu[dish_id]
                total_price += zomato.menu[dish_id]["price"]

        discount = zomato.coupons.get(coupon_code, 0)
        final_price = total_price - (total_price * discount / 100)
        order_id = str(zomato.order_id_counter)

        zomato.orders[order_id] = {
            "customer": customer_name,
            "dishes": ordered_dishes,
            "status": "received",
            "total_price": total_price,
            "discount": discount,
            "final_price": final_price
        }
        zomato.order_id_counter += 1
        zomato.save_data()
        return redirect(url_for("invoice", order_id=order_id))

    return render_template("order.html", menu=zomato.menu)

@app.route('/orders')
def view_orders():
    return render_template("orders.html", orders=zomato.orders)

@app.route('/update_status/<order_id>', methods=["POST"])
def update_status(order_id):
    new_status = request.form["status"]
    if order_id in zomato.orders:
        zomato.orders[order_id]["status"] = new_status
        zomato.save_data()
    return redirect(url_for("view_orders"))

@app.route('/invoice/<order_id>')
def invoice(order_id):
    order = zomato.orders.get(order_id)
    if not order:
        return "Order not found!", 404
    return render_template("invoice.html", order_id=order_id, order=order)

if __name__ == "__main__":
    app.run(debug=True)
