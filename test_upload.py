import os
import io
from app import app

# Test file upload functionality
app.config['TESTING'] = True

def test_file_upload():
    with app.test_client() as client:
        # Simulate login
        with client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['user_name'] = 'Test User'
            sess['user_email'] = 'test@example.com'

        # Create test files
        pfp_data = io.BytesIO(b'fake profile picture data')
        banner_data = io.BytesIO(b'fake banner data')

        data = {
            'bio': 'Test bio update',
            'profile_picture': (pfp_data, 'test_pfp.jpg'),
            'banner': (banner_data, 'test_banner.jpg'),
        }

        print("Sending POST request to /profile...")
        response = client.post('/profile', data=data, content_type='multipart/form-data')

        print(f"Response status: {response.status_code}")
        print(f"Response data: {response.data.decode('utf-8')}")

        # Check if files were created
        upload_folder = app.config['UPLOAD_FOLDER']
        pfp_path = os.path.join(upload_folder, 'test_pfp.jpg')
        banner_path = os.path.join(upload_folder, 'test_banner.jpg')

        print(f"Checking if PFP file exists: {pfp_path} - {os.path.exists(pfp_path)}")
        print(f"Checking if Banner file exists: {banner_path} - {os.path.exists(banner_path)}")

        if os.path.exists(pfp_path):
            with open(pfp_path, 'rb') as f:
                content = f.read()
                print(f"PFP file content: {content}")

        if os.path.exists(banner_path):
            with open(banner_path, 'rb') as f:
                content = f.read()
                print(f"Banner file content: {content}")

if __name__ == '__main__':
    test_file_upload()
