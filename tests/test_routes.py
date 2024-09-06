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
import string
import random

DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql://postgres:postgres@localhost:5432/postgres"
)

BASE_URL = "/accounts"


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

    ##################
    #  READ ACCOUNT  #
    ##################

    def test_read_an_account(self):
        """It should read an existing account"""
        # Create an account
        account = AccountFactory()
        response = self.client.post(
            BASE_URL,
            json=account.serialize(),
            content_type="application/json"
        )
        # Get id of posted account
        account_id = response.get_json()["id"]
        # GET the account from the REST endpoint
        response2 = self.client.get(
            f"{BASE_URL}/{account_id}",
            content_type="application/json"
        )
        # Check response code
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        # Get account data from response2
        account2 = response2.get_json()
        # Check data from account and account2 are identical
        self.assertEqual(account2["name"], account.name)
        self.assertEqual(account2["email"], account.email)
        self.assertEqual(account2["address"], account.address)
        self.assertEqual(account2["phone_number"], account.phone_number)
        self.assertEqual(account2["date_joined"], str(account.date_joined))

    def test_account_not_found(self):
        """Attempt to read an account that doesn't exist"""
        response = self.client.get(
            f"{BASE_URL}/0",
            content_type="application/json"
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    ####################
    #  UPDATE ACCOUNT  #
    ####################

    def test_update_account(self):
        """Attempt to update an existing Account"""
        # Create an account
        account = AccountFactory()
        # Post the account data
        response = self.client.post(
            BASE_URL,
            json=account.serialize(),
            content_type="application/json"
        )
        # Check response code for successful account creation in db
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # Get account data from response
        account_new = response.get_json()
        # Change the name by appending a random lower case letter (ensures uniqueness)
        name_new = account_new["name"]
        while True:
            name_new = name_new + random.choice(string.ascii_lowercase)
            if name_new != account_new["name"]:
                break
        account_new["name"] = name_new
        # Update the account in the db with a put request
        response2 = self.client.put(
            f"{BASE_URL}/{account_new['id']}",
            json=account_new
        )
        # Check the response code of the put request
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        # Get the updated account data from the response
        account_updated = response2.get_json()
        # Check that the name was successfully updated
        self.assertEqual(account_updated["name"], name_new)

    def test_update_account_not_found(self):
        """Attempt to update an account that doesn't exist"""
        # Create an account object
        account = AccountFactory()
        # Try to update account in the db wthat doesn't exist
        response = self.client.put(
            f"{BASE_URL}/0",
            json=account.serialize()
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    ####################
    #  DELETE ACCOUNT  #
    ####################

    def test_delete_account(self):
        """Delete an Account"""
        # Create an account
        account = AccountFactory()
        # Post the account data
        response = self.client.post(
            BASE_URL,
            json=account.serialize(),
            content_type="application/json"
        )
        # Check response code for successful account creation in db
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # Get account data from response
        account_new = response.get_json()
        # Delete the account
        response = self.client.delete(
            f"{BASE_URL}/{account_new['id']}"
        )
        # Check response code for successful deletion of account from db
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    ###################
    #  LIST ACCOUNTS  #
    ###################

    def test_get_accounts_list(self):
        """Get a list of all accounts"""
        # Use helper method to create 5 accounts
        self._create_accounts(5)
        # Attempt to get the list of accounts from the db
        response = self.client.get(
            f"{BASE_URL}",
            content_type="application/json"
        )
        # Check response code for successful get request
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Get the accounts data from the response
        accounts = response.get_json()
        # Check that 5 accounts were received in the response
        self.assertEqual(len(accounts), 5)

    ####################
    #  ERROR HANDLERS  #
    ####################

    def test_method_not_allowed(self):
        """Shouldn't allow illegal method calls"""
        # Use delete on a route that does not implement it
        response = self.client.delete(
            f"{BASE_URL}"
        )
        # Test the response code
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
