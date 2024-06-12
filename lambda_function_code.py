import os
import boto3
import psycopg2
import json
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from base64 import b64encode

# Secret key for encryption (replace with your own secret key)
SECRET_KEY = b'my_secret_key_123'

# Connect to localstack and PostgreSQL
sqs = boto3.client('sqs', endpoint_url='http://localhost:4566', region_name='us-east-1')
queue_url = 'http://localhost:4566/000000000000/login-queue'

conn = psycopg2.connect(
    dbname='postgres',
    user='postgres',
    password='postgres',
    host='localhost',
    port=5432
)


def encrypt_data(data, secret_key):
    """ Encrypt data using AES encryption """
    # Generate a salt and derive key and IV using PBKDF2
    salt = os.urandom(16)
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
        backend=default_backend()
    )
    key = kdf.derive(secret_key)
    iv = os.urandom(16)

    # Encrypt the data
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    padder = padding.PKCS7(algorithms.AES.block_size).padder()
    padded_data = padder.update(data.encode()) + padder.finalize()
    encrypted_data = encryptor.update(padded_data) + encryptor.finalize()

    # Encode the salt, iv, and encrypted data into a single string
    encrypted_message = b64encode(salt + iv + encrypted_data).decode('utf-8')
    return encrypted_message


def mask_pii(data):
    """ Mask PII data using reversible encryption """
    masked_data = data.copy()
    if 'device_id' in data and data['device_id']:
        masked_data['device_id'] = encrypt_data(data['device_id'], SECRET_KEY)
    else:
        masked_data['device_id'] = None

    if 'ip' in data and data['ip']:
        masked_data['ip'] = encrypt_data(data['ip'], SECRET_KEY)
    else:
        masked_data['ip'] = None

    return masked_data


def extract_app_version(version_str):
    """ Extract the integer part of the app version before the period """
    return int(version_str.split('.')[0]) if version_str and '.' in version_str else None


def lambda_handler(event, context):
    # Receive messages from SQS queue
    response = sqs.receive_message(
        QueueUrl=queue_url,
        MaxNumberOfMessages=10,
        WaitTimeSeconds=5
    )

    if 'Messages' not in response:
        print("No messages in queue")
        return

    messages = response['Messages']
    cursor = conn.cursor()

    for message in messages:
        body = json.loads(message['Body'])

        # Mask PII data
        masked_body = mask_pii(body)

        # Extract integer part of app version
        masked_body['app_version'] = extract_app_version(masked_body.get('app_version'))

        # Prepare SQL statement
        sql = """
        INSERT INTO user_logins (
            user_id, device_type, masked_ip, masked_device_id, locale, app_version, create_date
        ) VALUES (%s, %s, %s, %s, %s, %s, CURRENT_DATE)
        """
        cursor.execute(sql, (
            masked_body.get('user_id'),
            masked_body.get('device_type'),
            masked_body.get('ip'),
            masked_body.get('device_id'),
            masked_body.get('locale'),
            masked_body.get('app_version')
        ))

        # Uncomment the following line to delete the message from the queue after processing
        # sqs.delete_message(
        #     QueueUrl=queue_url,
        #     ReceiptHandle=message['ReceiptHandle']
        # )

    conn.commit()
    cursor.close()


if __name__ == "__main__":
    lambda_handler(None, None)
