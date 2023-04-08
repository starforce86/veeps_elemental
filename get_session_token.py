#!/usr/bin/env python3
import boto3

session = boto3.Session(profile_name="veeps")

iam_client = session.client("iam")
sts_client = session.client("sts")

aws_token_code = input("Input AWS token code: ")

mfa = iam_client.list_mfa_devices()

mfa_device = mfa["MFADevices"][0]["SerialNumber"]

aws_info = sts_client.get_session_token(
    DurationSeconds=129600,
    SerialNumber=mfa_device,
    TokenCode=aws_token_code,
)

AWS_ACCESS_KEY_ID = aws_info["Credentials"]["AccessKeyId"]
AWS_SECRET_ACCESS_KEY = aws_info["Credentials"]["SecretAccessKey"]
AWS_SESSION_TOKEN = aws_info["Credentials"]["SessionToken"]
print(f"""
AWS_ACCESS_KEY_ID={AWS_ACCESS_KEY_ID}
AWS_SECRET_ACCESS_KEY={AWS_SECRET_ACCESS_KEY}
AWS_SESSION_TOKEN={AWS_SESSION_TOKEN}
""")
