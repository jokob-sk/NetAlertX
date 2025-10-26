### Unit Tests

>[!WARNING]
> Please note these test modify data in the database. 

1. See the `/test` directory for available test cases. These are not exhaustive but cover the main API endpoints.  
2. To run a test case, SSH into the container:  
   `sudo docker exec -it netalertx /bin/bash`  
3. Inside the container, install pytest (if not already installed):  
   `pip install pytest`  
4. Run a specific test case:  
   `pytest /app/test/TESTFILE.py`