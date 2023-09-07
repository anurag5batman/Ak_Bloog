from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from flask import Flask


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///store.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


class Customer(db.Model):
    __tablename__ = 'customer'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    orders = relationship("Order", back_populates="customer")


class Order(db.Model):
    __tablename__ = 'order'
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'))
    customer = relationship("Customer", back_populates="orders")


with app.app_context():
    costumer = Customer()
    costumer.name = "ak"
    db.session.add(costumer)
    db.session.commit()

    order = Order()
    order.customer_id = 1
    db.session.add(order)
    db.session.commit()


customer = db.session.query(Customer).get(1)
orders = customer.orders

print(orders)