import os
from sqlalchemy import Column, String, Integer, create_engine
from flask_sqlalchemy import SQLAlchemy
import json


db = SQLAlchemy()

class Product(db.Model):
    __tablename__ = 'product'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(1000), nullable=False)
    image = db.Column(db.String(), nullable=False)
    category = db.Column(db.String(100), nullable=False)
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime, nullable=False)
    live = db.Column(db.Boolean, nullable=False)
    price = db.Column(db.Float, nullable=False)
    owner = db.Column(db.VARCHAR(), db.ForeignKey('user.email'), nullable=False)
    bid_by = db.Column(db.VARCHAR(), db.ForeignKey('user.email'), nullable=True)
    winner = db.Column(db.String(100), nullable=True)

    def __repr__(self):
        return f'<Product {self.id} {self.name} {self.description} {self.category} {self.price} {self.owner} {self.bid_by}>'

class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.VARCHAR(), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(120), nullable=True)
    address = db.Column(db.String(120), nullable=True)

    def __repr__(self):
        return f'<User {self.id} {self.name} {self.email} {self.password} {self.phone} {self.address}>'

