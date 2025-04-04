"""
Account Service

This microservice handles the lifecycle of Accounts
"""
# pylint: disable=unused-import
from flask import jsonify, request, make_response, abort, url_for   # noqa; F401
from service.models import Account
from service.common import status  # HTTP Status Codes
from . import app  # Import Flask application


############################################################
# Health Endpoint
############################################################
@app.route("/health")
def health():
    """Health Status"""
    return jsonify(dict(status="OK")), status.HTTP_200_OK


######################################################################
# GET INDEX
######################################################################
@app.route("/")
def index():
    """Root URL response"""
    return (
        jsonify(
            name="Account REST API Service",
            version="1.0",
            # paths=url_for("list_accounts", _external=True),
        ),
        status.HTTP_200_OK,
    )


######################################################################
# CREATE A NEW ACCOUNT
######################################################################
@app.route("/accounts", methods=["POST"])
def create_accounts():
    """
    Creates an Account
    This endpoint will create an Account based the data in the body that is posted
    """
    app.logger.info("Request to create an Account")
    check_content_type("application/json")
    account = Account()
    account.deserialize(request.get_json())
    account.create()
    message = account.serialize()
    # Uncomment once get_accounts has been implemented
    # location_url = url_for("get_accounts", account_id=account.id, _external=True)
    location_url = "/"  # Remove once get_accounts has been implemented
    return make_response(
        jsonify(message), status.HTTP_201_CREATED, {"Location": location_url}
    )

######################################################################
# LIST ALL ACCOUNTS
######################################################################


# ... place you code here to LIST accounts ...
@app.route("/accounts", methods=["GET"])
def list_accounts():
    """
    Method to return list of all accounts as dictionaries
    """
    app.logger.info("Request to list accounts in Database")
    accs = Account.all()
    out = []
    for acc in accs:
        out.append(acc.serialize())
    return make_response(jsonify(out), status.HTTP_200_OK)

######################################################################
# READ AN ACCOUNT
######################################################################


# ... place you code here to READ an account ...
@app.route("/accounts/<int:id>", methods=["GET"])
def read_account(id):
    """
    Method to handle the RESTful API endpoints for retrieving an account by ID reference
    """
    app.logger.info("Request to retrieve account with id %s", id)
    acc = Account.find(id)
    if(not acc):
        abort(status.HTTP_404_NOT_FOUND)
    out = acc.serialize()
    return make_response(out, status.HTTP_200_OK)

######################################################################
# UPDATE AN EXISTING ACCOUNT
######################################################################


# ... place you code here to UPDATE an account ...
@app.route("/accounts/<int:id>", methods=["PUT"])
def update_account(id):
    """
    Method to update an account in the database
    """
    find_account = Account.find(id)
    if(not find_account):
        return make_response("", status.HTTP_404_NOT_FOUND)
    new_data = request.get_json()
    find_account.deserialize(new_data)
    find_account.update()
    return make_response(Account.find(id).serialize(), status.HTTP_200_OK)

######################################################################
# DELETE AN ACCOUNT
######################################################################


# ... place you code here to DELETE an account ...
@app.route("/accounts/<int:id>", methods=["DELETE"])
def delete_account(id):
    """
    Method to use RESTful DELETE endpoint to delete an account from the database
    """
    app.logger.info("Request to delete account with id %s", id)
    acc = Account.find(id)
    if(acc):
        acc.delete()
    return make_response("", status.HTTP_204_NO_CONTENT)

######################################################################
#  U T I L I T Y   F U N C T I O N S
######################################################################


def check_content_type(media_type):
    """Checks that the media type is correct"""
    content_type = request.headers.get("Content-Type")
    if content_type and content_type == media_type:
        return
    app.logger.error("Invalid Content-Type: %s", content_type)
    abort(
        status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
        f"Content-Type must be {media_type}",
    )
