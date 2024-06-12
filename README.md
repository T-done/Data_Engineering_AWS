# Fetch Rewards Data Engineering Take Home

## Overview

This project involves reading JSON data containing user login behavior from an AWS SQS Queue, masking PII data, and writing the transformed data to a Postgres database. The application is designed to run locally using Docker and Docker Compose.

## Project Structure

data-engineering-take-home/


├── docker-compose.yml

├── lambda_function_code.py

├── README.md

└── requirements.txt

## Setup

1. **Install Required Tools:**
    - Docker
    - Docker Compose
    - AWS CLI (with `awscli-local`)
    - PostgreSQL CLI (`psql`)

2. **Clone the Docker Images:**
    - Fetch Rewards Localstack Image: `fetchdocker/data-takehome-localstack`
    - Fetch Rewards Postgres Image: `fetchdocker/data-takehome-postgres`

3. **Create `docker-compose.yml`:**
    ```yaml
    version: "3.9"
    services:
      localstack:
        image: fetchdocker/data-takehome-localstack
        ports:
          - "4566:4566"
      postgres:
        image: fetchdocker/data-takehome-postgres
        ports:
          - "5432:5432"
        environment:
          POSTGRES_USER: postgres
          POSTGRES_PASSWORD: postgres
    ```

4. **Create Python Script (`f_code.py`) to Simulate AWS Lambda Function:**
    - See the provided `lambda_function_code.py` script.

5. **Run Docker Containers:**
    ```sh
    docker-compose up
    ```

6. **Install Python Dependencies:**
    ```sh
    pip install -r requirements.txt
    ```

    **Note:** Ensure compatibility between `boto3` and `localstack` versions. For this setup, we have used `localstack` version `0.14.3.1` which is compatible with `boto3==1.18.*`.

7. **Test the Lambda Function:**
    ```sh
    python lambda_function_code.py
    ```

## Assumptions

- The SQS queue and Postgres database are running locally using Docker.
- PII data is masked using MD5 hashing for uniqueness.
- The `app_version` is stored as an integer, representing the part before the period.
- Proper error handling is implemented for missing keys.

## Key Decisions

### How will you read messages from the queue?
- Used the `boto3` library to interact with the SQS queue.

### What type of data structures should be used?
- Used Python dictionaries to handle JSON data.

### How will you mask the PII data so that duplicate values can be identified?
- Used MD5 hashing to mask `device_id` and `ip`, ensuring consistent hashing to identify duplicates.

### What will be your strategy for connecting and writing to Postgres?
- I have used the `psycopg2` library to connect and execute SQL statements to insert data into the Postgres database.

### Where and how will your application run?
- The application will run locally using Docker for both SQS and Postgres services. The Python script simulates the AWS Lambda function.

## Questions

### How would you deploy this application in production?
- Deploy the function using AWS Lambda and use Amazon RDS for the Postgres database. Configure SQS to trigger the Lambda function automatically.

### What other components would you want to add to make this production ready?
- Add logging and monitoring (e.g., CloudWatch).
- Implement robust error handling and retries.
- Secure the database and data transmission (e.g., using IAM roles, SSL).

### How can this application scale with a growing dataset?
- Scale the Lambda function automatically based on the number of messages in the SQS queue. AWS Lambda supports automatic scaling based on the number of incoming requests (in this case, SQS messages).

### How can PII be recovered later on?
- PII (Personally Identifiable Information) can be recovered later on by decrypting the masked data using AES (Advanced Encryption Standard) encryption with CBC (Cipher Block Chaining) mode. The encryption is performed using a secret key (SECRET_KEY) that is securely stored and managed. When decryption is required, the original PII values, such as device_id and ip, can be retrieved by applying the decryption process with the same SECRET_KEY that was used for encryption during masking. This ensures that the reversible masking technique maintains data security while allowing for the recovery of original PII values when needed.

## Next Steps

- Add logging and monitoring.
- Implement unit tests and integration tests.
- Optimize data transformation and masking logic.
- Uncomment the `sqs.delete_message` line in the script to enable message deletion after processing.
