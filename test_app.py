from app import app

def test_home():
    response = app.test_client().get('/')
    assert response.status_code == 200
    assert b"Hello, Flask CI/CD is running successfully on EC2 with Jenkins and Nginx!" in response.data
