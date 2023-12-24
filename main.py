from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
import os
from sqlalchemy.exc import SQLAlchemyError
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

# Create a Flask app
app = Flask(__name__)

# Configure the database
database_uri = os.getenv(
    'DATABASE_URL', 'mysql+pymysql://user:password@localhost/mydatabase')
app.config['SQLALCHEMY_DATABASE_URI'] = database_uri
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_POOL_RECYCLE'] = 280
app.config['SQLALCHEMY_POOL_TIMEOUT'] = 20

db = SQLAlchemy(app)

# Define the InputYahoo model


class InputYahoo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.String(1000), unique=True, nullable=False)

# Define the OutputYahooSuccess model


class OutputYahooSuccess(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.String(1000), unique=True, nullable=False)

# Define the OutputYahooFail model


class OutputYahooFail(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.String(1000), unique=True, nullable=False)

# Define the Output model


class Output(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.String(1000), unique=True, nullable=False)

# Define the KeyApi model


class KeyApi(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.String(1000), unique=True, nullable=False)

# Function to add a new record


@app.route('/add/<model_name>', methods=['POST'])
def add_record(model_name):
    json_data = request.json
    data = json_data.get('data')
    model = get_model_by_name(model_name)

    if model and data:
        try:
            new_record = model(data=data)
            db.session.add(new_record)
            db.session.commit()
            return jsonify({"message": "Record added successfully", "id": new_record.id}), 201
        except SQLAlchemyError as e:
            db.session.rollback()
            logging.error(f"Database error: {e}")
            return jsonify({"message": "Database error occurred"}), 500
    return jsonify({"message": "Invalid model name or data"}), 400

# Function to retrieve all records


@app.route('/view/<model_name>')
def view_records(model_name):
    model = get_model_by_name(model_name)
    if model:
        records = model.query.all()
        return jsonify([{"id": record.id, "data": record.data} for record in records])
    return jsonify({"message": "Invalid model name"}), 404

# Function to update a record


@app.route('/update/<model_name>/<int:id>', methods=['PUT'])
def update_record(model_name, id):
    data = request.json
    new_data = data.get('data')
    model = get_model_by_name(model_name)

    if model and new_data:
        record = model.query.get(id)
        if record:
            record.data = new_data
            db.session.commit()
            return jsonify({"message": "Record updated successfully"})
        return jsonify({"message": "Record not found"}), 404
    return jsonify({"message": "Invalid model name or new data"}), 400

# Function to delete a record


@app.route('/delete/<model_name>/<int:id>', methods=['DELETE'])
def delete_record(model_name, id):
    model = get_model_by_name(model_name)
    if model:
        record = model.query.get(id)
        if record:
            db.session.delete(record)
            db.session.commit()
            return jsonify({"message": "Record deleted successfully"})
        return jsonify({"message": "Record not found"}), 404
    return jsonify({"message": "Invalid model name"}), 400


@app.route('/view/<model_name>/first')
def view_first_record(model_name):
    model = get_model_by_name(model_name)
    if model:
        record = model.query.first()  # Corrected to 'first()' and removed '.all()'
        if record:
            return jsonify({"id": record.id, "data": record.data})
        else:
            return jsonify({"message": "No records found"}), 404
    return jsonify({"message": "Invalid model name"}), 404


@app.route('/pop/<model_name>', methods=['GET'])
def pop_record(model_name):
    model = get_model_by_name(model_name)
    if model:
        record = model.query.order_by(model.id).first()  # Or order by 'id'
        if record:
            record_data = {"id": record.id, "data": record.data}
            db.session.delete(record)
            db.session.commit()
            return jsonify(record_data)
        return jsonify({"message": "No records to pop"}), 404
    return jsonify({"message": "Invalid model name"}), 400

# Utility function to get model by its name


def get_model_by_name(name):
    if name.lower() == 'inputyahoo':
        return InputYahoo
    elif name.lower() == 'outputyahoosuccess':
        return OutputYahooSuccess
    elif name.lower() == 'outputyahoofail':
        return OutputYahooFail
    elif name.lower() == 'output':
        return Output
    elif name.lower() == 'keyapi':
        return KeyApi
    return None


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', debug=True)
