from lib.google_auth import get_creds

if __name__ == "__main__":
    creds = get_creds()
    print("Successfully obtained Google API credentials.")