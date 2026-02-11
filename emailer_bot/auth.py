import msal
import logging

class MicrosoftAuth:
    # This is a placeholder. Users must provide their own Client ID if this is not a registered multi-tenant app.
    # For personal use, users should register an app in Azure Portal as "Mobile and desktop applications"
    # and use that Client ID.
    DEFAULT_CLIENT_ID = "YOUR_CLIENT_ID_HERE"

    SCOPES = ["User.Read", "Mail.ReadWrite", "Mail.Send", "Files.Read.All", "offline_access"]
    AUTHORITY = "https://login.microsoftonline.com/common"

    def __init__(self, client_id: str = None, token_cache=None):
        self.client_id = client_id or self.DEFAULT_CLIENT_ID
        self.app = msal.PublicClientApplication(
            self.client_id,
            authority=self.AUTHORITY,
            token_cache=token_cache
        )

    def login(self):
        """Interactive login flow."""
        # This will open the system browser
        result = self.app.acquire_token_interactive(scopes=self.SCOPES)
        if "error" in result:
             raise Exception(f"Login failed: {result.get('error_description')}")
        return result

    def get_access_token_silently(self, username=None):
        """Try to get token from cache."""
        accounts = self.app.get_accounts()
        target_account = None

        if username:
             # Find specific account
             for a in accounts:
                 if a.get("username") == username:
                     target_account = a
                     break
        elif accounts:
            target_account = accounts[0]

        if target_account:
            result = self.app.acquire_token_silent(self.SCOPES, account=target_account)
            if result:
                return result
        return None

    def refresh_access_token(self, refresh_token):
        """Refresh token using a refresh token string."""
        # Note: acquire_token_by_refresh_token is technically available in ClientApplication
        # but normally used for ConfidentialClient. For PublicClient, it works too.
        result = self.app.acquire_token_by_refresh_token(refresh_token, scopes=self.SCOPES)
        if "error" in result:
             raise Exception(f"Refresh failed: {result.get('error_description')}")
        return result

def generate_oauth2_string(username, access_token):
    """Generates the XOAUTH2 string for IMAP/SMTP authentication."""
    auth_string = f"user={username}\x01auth=Bearer {access_token}\x01\x01"
    return auth_string
