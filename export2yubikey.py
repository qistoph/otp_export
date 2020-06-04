#!/usr/bin/python3
# -*- coding: future_fstrings -*-

import sys
from urllib.parse import urlparse, parse_qs
from base64 import b64decode, b32encode

import OtpMigration_pb2 as otp

def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

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

for params in payload.otp_parameters:

    ykargs = ["oath","add"]

    otp_type = otp.OtpType.Name(params.type)
    ykargs.extend(["-o", otp_type])

    if params.digits == otp.DigitCount.SIX:
        otp_digits = "6"
    elif params.digits == otp.DigitCount.EIGHT:
        otp_digits = "8"
    else:
        raise Exception(f"Unexpected DigitCount: {otp.DigitCount.Name(params.digits)}")
    ykargs.extend(["-d", otp_digits])

    otp_algorirthm = otp.Algorithm.Name(params.algorithm)
    ykargs.extend(["-a", otp_algorirthm])

    if params.type == otp.OtpType.HOTP:
        ykargs.extend(["-c", params.counter])
    elif params.type == otp.OtpType.TOTP:
        ykargs.extend(["-p", "30"])
    else:
        raise Exception(f"Unexpected OtpType: {otp.OtpType.Name(params.type)}")

    if len(params.issuer) > 0:
        ykargs.extend(["-i", '"'+params.issuer+'"'])

    ykargs.append('"' + params.name + '"')

    ykargs.append(b32encode(params.secret).decode("UTF-8"))

    #print(ykargs)
    print("ykman " + " ".join(ykargs))
