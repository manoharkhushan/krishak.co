from app import app

# Test profile page access
app.config['TESTING'] = True

def test_profile_page_access():
    with app.test_client() as client:
        # Test without login - should redirect to login
        response = client.get('/profile')
        print(f"Without login - Status: {response.status_code}, Location: {response.headers.get('Location')}")

        # Simulate login
        with client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['user_name'] = 'Test User'
            sess['user_email'] = 'test@example.com'

        # Test with login - should load profile page
        response = client.get('/profile')
        print(f"With login - Status: {response.status_code}")
        if response.status_code == 200:
            print("Profile page loaded successfully")
            # Check if it contains expected content
            if b"My Profile" in response.data:
                print("Profile page content is correct")
            else:
                print("Profile page content may be incorrect")
                print("Response data preview:", response.data[:500])
        else:
            print("Profile page failed to load")
            print("Response data:", response.data.decode('utf-8'))

if __name__ == '__main__':
    test_profile_page_access()
