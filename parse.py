#!/usr/bin/python3

import sys
from urllib.parse import urlparse, parse_qs, quote
from base64 import b64decode, b32encode

import OtpMigration_pb2 as otp

def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

def num_digits(digit_count):
    if digit_count == otp.DigitCount.SIX:
        return 6
    if digit_count == otp.DigitCount.EIGHT:
        return 8

    raise ValueError('Invalid DigitCount, expecting SIX or EIGHT')

if len(sys.argv) < 2:
    eprint("Usage: {0} <data>".format(sys.argv[0]))
    eprint("<data> should be a otpauth-migration:// url")
    sys.exit(1)

url = urlparse(sys.argv[1])

if url.scheme != 'otpauth-migration':
    eprint("Only otpauth-migration URLs can be parsed")
    sys.exit(2)

qs = parse_qs(url.query)

if 'data' not in qs:
    eprint("Missing `data` field in query string")
    sys.exit(3)

data = b64decode(qs["data"][0])
payload = otp.MigrationPayload.FromString(data)

print("version:", payload.version)
print("batch_size:", payload.batch_size)
print("batch_index:", payload.batch_index)
print("batch_id:", payload.batch_id)
print("otp_parameters:")
for params in payload.otp_parameters:
    otpauth_url = "otpauth://"
    otpauth_url += otp.OtpType.Name(params.type).lower()
    otpauth_url += "/"
    otpauth_url += quote(params.issuer)
    otpauth_url += ":"
    otpauth_url += quote(params.name)
    otpauth_url += "?secret=" + b32encode(params.secret).decode()
    otpauth_url += "&issuer=" + quote(params.issuer)
    otpauth_url += "&algorithm=" + otp.Algorithm.Name(params.algorithm).lower()
    otpauth_url += "&digits=" + str(num_digits(params.algorithm))
    otpauth_url += "&counter=" + str(params.counter)
    print("  " + otpauth_url)

    print("  secret:", b32encode(params.secret))
    print("  name:", params.name)
    print("  issuer:", params.issuer)
    print("  algorithm:", otp.Algorithm.Name(params.algorithm))
    print("  digits:", otp.DigitCount.Name(params.digits))
    print("  type:", otp.OtpType.Name(params.type))
    print("  counter:", params.counter)
    print()
