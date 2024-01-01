from random import choice
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
import os
from pymysql import IntegrityError
from sqlalchemy.exc import SQLAlchemyError
import logging
from functools import wraps


# Configure logging
logging.basicConfig(level=logging.INFO)

# Create a Flask app
app = Flask(__name__)

api_key = os.getenv('KEY_API', 'hellocacban123123')
flask_port = os.getenv('FLASK_PORT', 5000)

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


class Hotmail(db.Model):
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


class KeyApi(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.String(1000), unique=True, nullable=False)

# Define the KeyApi model


class Pickle(db.Model):
    username = db.Column(db.String(200), primary_key=True)
    data = db.Column(db.Text(), nullable=False)


def auth_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        _api_key = request.headers.get('X-API-KEY')  # Custom header for API key
        if _api_key != api_key:  # Replace with your actual API key
            return jsonify({"message": "Unauthorized"}), 401
        return f(*args, **kwargs)
    return decorated_function


@app.route('/', methods=['GET'])
def index():
    return jsonify({"message": "Live"}), 200

# Function to add a new record


@app.route('/add_pickle', methods=['POST'])
@auth_required
def add_pickle():
    json_data = request.json
    username = json_data.get('username')
    data = json_data.get('data')

    if not username or not data:
        return jsonify({"message": "Username and data are required"}), 400

    new_pickle = Pickle(username=username, data=data)

    try:
        db.session.add(new_pickle)
        db.session.commit()
        return jsonify({"message": "Pickle added successfully"}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": str(e)}), 500


@app.route('/pickles', methods=['GET'])
@auth_required
def get_pickles():
    all_pickles = Pickle.query.all()
    return jsonify([{'username': pickle.username, 'data': pickle.data} for pickle in all_pickles])


@app.route('/pickle/<username>', methods=['GET'])
@auth_required
def get_pickle(username):
    pickle = Pickle.query.get(username)
    if pickle:
        return jsonify({'username': pickle.username, 'data': pickle.data})
    else:
        return jsonify({"message": "Pickle not found"}), 404


@app.route('/update_pickle/<username>', methods=['PUT'])
@auth_required
def update_pickle(username):
    pickle = Pickle.query.get(username)
    json_data = request.json
    data = json_data.get('data')

    if not pickle:
        return jsonify({"message": "Pickle not found"}), 404

    if data:
        pickle.data = data
        try:
            db.session.commit()
            return jsonify({"message": "Pickle updated successfully"})
        except Exception as e:
            db.session.rollback()
            return jsonify({"message": str(e)}), 500
    else:
        return jsonify({"message": "No data provided"}), 400


@app.route('/delete_pickle/<username>', methods=['DELETE'])
@auth_required
def delete_pickle(username):
    pickle = Pickle.query.get(username)
    if pickle:
        try:
            db.session.delete(pickle)
            db.session.commit()
            return jsonify({"message": "Pickle deleted successfully"})
        except Exception as e:
            db.session.rollback()
            return jsonify({"message": str(e)}), 500
    else:
        return jsonify({"message": "Pickle not found"}), 404


@app.route('/add/<model_name>', methods=['POST'])
@auth_required
def add_record(model_name):
    json_data = request.json  # Expecting a list of dictionaries
    model = get_model_by_name(model_name)
    if not model or not isinstance(json_data, list):
        return jsonify({"message": "Invalid model name or data"}), 400
    batch_size = 100
    total_added = 0
    errors = []
    for i in range(0, len(json_data), batch_size):
        batch = json_data[i:i + batch_size]
        for item in batch:
            data = item.get('data')
            if data:
                try:
                    new_record = model(data=data)
                    db.session.add(new_record)
                except IntegrityError as e:
                    db.session.rollback()
                    logging.error(f"Integrity error for record with data {data}: {e}")
                    errors.append({"data": data, "error": "Duplicate or invalid data"})
                    continue  # Skip this record and continue with the next
                except SQLAlchemyError as e:
                    # Handle general database errors
                    db.session.rollback()
                    logging.error(f"Database error for record with data {data}: {e}")
                    errors.append({"data": data, "error": str(e)})
                    continue  # Skip this record and continue with the next
        try:
            db.session.commit()
            total_added += len(batch) - len([error['data'] for error in errors])
        except SQLAlchemyError as e:
            db.session.rollback()
            logging.error(f"Failed to commit batch: {e}")
            for item in batch:
                data = item.get('data')
                if data and not any(error['data'] == data for error in errors):
                    errors.append({"data": data, "error": "Failed to commit batch"})
    response_message = {"message": f"Total records added: {total_added}"}
    if errors:
        response_message["errors"] = errors
    return jsonify(response_message), 201 if total_added else 500

# Function to retrieve all records


@app.route('/view/<model_name>')
@auth_required
def view_records(model_name):
    model = get_model_by_name(model_name)
    if model:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        paginated_records = model.query.paginate(page=page, per_page=per_page, error_out=False)
        records = [{"id": record.id, "data": record.data} for record in paginated_records.items]
        pagination_info = {
            "total_records": paginated_records.total,
            "total_pages": paginated_records.pages,
            "current_page": paginated_records.page,
            "records_per_page": per_page
        }
        return jsonify({"records": records, "pagination_info": pagination_info})
    return jsonify({"message": "Invalid model name"}), 404

# Function to update a record


@app.route('/update/<model_name>/<int:id>', methods=['PUT'])
@auth_required
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
@auth_required
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
@auth_required
def view_random_record(model_name):
    model = get_model_by_name(model_name)
    if model:
        records = model.query.all()  # Retrieve all records
        if records:
            record = choice(records)  # Select a random record
            return jsonify({"id": record.id, "data": record.data})
        else:
            return jsonify({"message": "No records found"}), 404
    return jsonify({"message": "Invalid model name"}), 404


@app.route('/pop/<model_name>', methods=['GET'])
@auth_required
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
    elif name.lower() == 'hotmail':
        return Hotmail
    elif name.lower() == 'keyapi':
        return KeyApi
    return None


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', debug=True,port=flask_port)
