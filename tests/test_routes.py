"""
Account API Service Test Suite

Test cases can be run with the following:
  nosetests -v --with-spec --spec-color
  coverage report -m
"""
import os
import logging
from unittest import TestCase
from tests.factories import AccountFactory
from service.common import status  # HTTP Status Codes
from service.models import db, Account, init_db
from service.routes import app
from service import talisman

DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql://postgres:postgres@localhost:5432/postgres"
)

BASE_URL = "/accounts"
HTTPS_ENVIRON = {'wsgi.url_scheme': 'https'}


######################################################################
#  T E S T   C A S E S
######################################################################


class TestAccountService(TestCase):
    """Account Service Tests"""

    @classmethod
    def setUpClass(cls):
        """Run once before all tests"""
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        init_db(app)
        talisman.force_https = False

    @classmethod
    def tearDownClass(cls):
        """Runs once before test suite"""

    def setUp(self):
        """Runs before each test"""
        db.session.query(Account).delete()  # clean up the last tests
        db.session.commit()

        self.client = app.test_client()

    def tearDown(self):
        """Runs once after each test case"""
        db.session.remove()

    ######################################################################
    #  H E L P E R   M E T H O D S
    ######################################################################

    def _create_accounts(self, count):
        """Factory method to create accounts in bulk"""
        accounts = []
        for _ in range(count):
            account = AccountFactory()
            response = self.client.post(BASE_URL, json=account.serialize())
            self.assertEqual(
                response.status_code,
                status.HTTP_201_CREATED,
                "Could not create test Account",
            )
            new_account = response.get_json()
            account.id = new_account["id"]
            accounts.append(account)
        return accounts

    ######################################################################
    #  A C C O U N T   T E S T   C A S E S
    ######################################################################

    def test_index(self):
        """It should get 200_OK from the Home Page"""
        response = self.client.get("/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_health(self):
        """It should be healthy"""
        resp = self.client.get("/health")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data["status"], "OK")

    def test_create_account(self):
        """It should Create a new Account"""
        account = AccountFactory()
        response = self.client.post(
            BASE_URL,
            json=account.serialize(),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Make sure location header is set
        location = response.headers.get("Location", None)
        self.assertIsNotNone(location)

        # Check the data is correct
        new_account = response.get_json()
        self.assertEqual(new_account["name"], account.name)
        self.assertEqual(new_account["email"], account.email)
        self.assertEqual(new_account["address"], account.address)
        self.assertEqual(new_account["phone_number"], account.phone_number)
        self.assertEqual(new_account["date_joined"], str(account.date_joined))

    def test_bad_request(self):
        """It should not Create an Account when sending the wrong data"""
        response = self.client.post(BASE_URL, json={"name": "not enough data"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unsupported_media_type(self):
        """It should not Create an Account when sending the wrong media type"""
        account = AccountFactory()
        response = self.client.post(
            BASE_URL,
            json=account.serialize(),
            content_type="test/html"
        )
        self.assertEqual(response.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    def test_method_not_allowed(self):
        """It should not do anything when an invalid method is used for a given URL pathway"""
        response = self.client.post(BASE_URL + "/0")
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    # ADD YOUR TEST CASES HERE ...

    def test_read_an_account(self):
        """It should retrieve by ID the same account it added to the database"""
        account = AccountFactory()
        response = self.client.post(
            BASE_URL,
            json=account.serialize(),
            content_type="application/json"
        )
        id = response.get_json()["id"]
        read_response = self.client.get(BASE_URL + "/" + str(id))
        self.assertEqual(read_response.status_code, status.HTTP_200_OK)
        self.assertEqual(read_response.get_json()["name"], account.name)

    def test_account_not_found(self):
        """It should receive an HTTP 404 error code for reading a non-existent account"""
        read_response = self.client.get(BASE_URL + "/0")
        self.assertEqual(read_response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_account(self):
        """It should remove a specified account from the database"""
        account = AccountFactory()
        response = self.client.post(
            BASE_URL,
            json=account.serialize(),
            content_type="application/json"
        )
        id = response.get_json()["id"]
        read_response = self.client.get(BASE_URL + "/" + str(id))
        self.assertEqual(read_response.status_code, status.HTTP_200_OK)
        self.assertEqual(read_response.get_json()["name"], account.name)
        delete_response = self.client.delete(BASE_URL + "/" + str(id))
        self.assertEqual(delete_response.status_code, status.HTTP_204_NO_CONTENT)
        read_response = self.client.get(BASE_URL + "/" + str(id))
        self.assertEqual(read_response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_account_not_found(self):
        """It should not change anything in the database and receive the same 204 response"""
        delete_response = self.client.delete(BASE_URL + "/0")
        self.assertEqual(delete_response.status_code, status.HTTP_204_NO_CONTENT)

    def test_list_accounts(self):
        """It should retrieve a list of dictionaries of the accounts in the database"""
        acc_one = AccountFactory()
        acc_two = AccountFactory()
        self.client.post(
            BASE_URL,
            json=acc_one.serialize(),
            content_type="application/json"
        )
        self.client.post(
            BASE_URL,
            json=acc_two.serialize(),
            content_type="application/json"
        )
        response = self.client.get(BASE_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        self.assertEqual(len(data), 2)
        test_acc = data[0]
        if(test_acc["name"] == acc_one.name):
            self.assertEqual(test_acc["name"], acc_one.name)
        else:
            self.assertEqual(test_acc["name"], acc_two.name)

    def test_list_accounts_none_found(self):
        """It should retrieve an empty list when the database is empty"""
        response = self.client.get(BASE_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.get_json(), [])

    def test_update_accounts(self):
        """It should update an account via a put endpoint with an id and new account info"""
        acc = AccountFactory()
        response = self.client.post(
            BASE_URL,
            json=acc.serialize(),
            content_type="application/json"
        )
        acc_new = AccountFactory()
        id = str(response.get_json()["id"])
        put_response = self.client.put(
            BASE_URL + "/" + id,
            json=acc_new.serialize(),
            content_type="application/json"
        )
        self.assertEqual(put_response.status_code, status.HTTP_200_OK)
        get_response = self.client.get(BASE_URL + "/" + id)
        self.assertEqual(get_response.get_json()["name"], acc_new.name)

    def test_update_accounts_not_found(self):
        """It should fail to update an account that is misidentified via id"""
        acc = AccountFactory()
        response = self.client.put(
            BASE_URL + "/0",
            json=acc.serialize(),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_security_headers(self):
        """It should return the security headers for this program server"""
        response = self.client.get("/", environ_overrides=HTTPS_ENVIRON)
        data = response.headers
        self.assertEqual(data.get("X-Frame-Options"), "SAMEORIGIN")
        self.assertEqual(data.get("X-Content-Type-Options"), "nosniff")
        self.assertEqual(data.get("Content-Security-Policy"), "default-src 'self'; object-src 'none'")
        self.assertEqual(data.get("Referrer-Policy"), "strict-origin-when-cross-origin")

    def test_CORS_policies(self):
        """It should return the header "Access-Control-Allow-Origin:*"""
        response = self.client.get("/", environ_overrides=HTTPS_ENVIRON)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.headers.get("Access-Control-Allow-Origin"), "*")
