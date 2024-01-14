#!/usr/bin/python3

import argparse
from urllib.parse import urlparse, parse_qs, quote, unquote
from base64 import b64decode, b32encode
import OtpMigration_pb2 as otp
import os, sys


def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


def num_digits(digit_count):
    if digit_count == otp.DigitCount.SIX:
        return 6
    if digit_count == otp.DigitCount.EIGHT:
        return 8
    raise ValueError('Invalid DigitCount, expecting SIX or EIGHT')


def parse_url(url):
    parsed_url = urlparse(url)
    if parsed_url.scheme != 'otpauth-migration':
        raise TypeError("Only otpauth-migration URLs can be parsed")
    qs = parse_qs(parsed_url.query)
    if 'data' not in qs:
        raise ValueError("Missing `data` field in query string")
    data = unquote(qs['data'][0])
    return data


def process_url(url_input):
    try:
        data = parse_url(url_input)
    except (TypeError, ValueError) as e:
        eprint(e)
        return None

    decoded_data = decode_qs(data)
    payload = otp.MigrationPayload.FromString(decoded_data)
    return decode_secrets(payload)


def decode_qs(data):
    decoded_url_data = unquote(data)
    return b64decode(decoded_url_data)


def decode_secrets(payload):
    if not str(type(payload)) == "<class 'OtpMigration_pb2.MigrationPayload'>":
        payload = otp.MigrationPayload.FromString(payload)
    _data = []
    _data.append(f"version: {payload.version}")
    _data.append(f"batch_size: {payload.batch_size}")
    _data.append(f"batch_index: {payload.batch_index}")
    _data.append(f"batch_id: {payload.batch_id}")
    _data.append("otp_parameters:")
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
        _data.append(f"  {otpauth_url}")
        _data.append(f"  secret: {b32encode(params.secret)}")
        _data.append(f"  name: {params.name}")
        _data.append(f"  issuer: {params.issuer}")
        _data.append(f"  algorithm: {otp.Algorithm.Name(params.algorithm)}")
        _data.append(f"  digits: {otp.DigitCount.Name(params.digits)}")
        _data.append(f"  type: {otp.OtpType.Name(params.type)}")
        _data.append(f"  counter: {params.counter}"+"\n")
    return "\n".join(_data)


def main():
    parser = argparse.ArgumentParser(description='Decode otpauth-migration URLs.')
    parser.add_argument('input', help='otpauth-migration:// URL or path to a text file containing the URLs')
    parser.add_argument('--file', action='store_true', help='Indicates that the input is a file path')
    parser.add_argument('--output', help='Path to a text file where the output will be written (optional)')
    args = parser.parse_args()

    results = []

    if args.file:
        if not os.path.exists(args.input):
            eprint(f"File not found: {args.input}")
            sys.exit(4)
        with open(args.input, 'r') as file:
            for line in file:
                url_input = line.strip()
                if url_input:  # Skip blank lines
                    result = process_url(url_input)
                    if result is not None:
                        results.append(result)
    else:
        result = process_url(args.input)
        if result is not None:
            results.append(result)

    output_text = "\n".join(results)

    if args.output:
        with open(args.output, 'w') as file:
            file.write(output_text)
        print(f"Output written to {args.output}")
    else:
        print(output_text)




if __name__ == "__main__":
    main()
