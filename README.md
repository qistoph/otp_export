# Google Authenticator export format

A recent update of the [Google Authenticator](https://play.google.com/store/apps/details?id=com.google.android.apps.authenticator2) app on Android brought an export/import feature. This enables users to copy their 2FA codes to a new device.

The format of the export seems to not be publicly documented (yet?). I believe that this export function is quite interesting and would like to see innovative solutions for back-up or interopability between devices. It would also be in the general public's interest if there would be a single import/export format for 2FA codes and this one looks promising to me.

This repo contains my interpretation of the export data. I hope this enables other developers to come up with new cool solutions that use the exported secrets.

** **NOTE THAT THE 2FA CODES ARE SECRETS THAT YOU SHOULD TREAT AS SUCH!** **

An interesting blog about the update was published at [Ctrl blog](https://www.ctrl.blog/entry/google-authenticator-2fa-secrets.html).

## Encapsulation

The layers of data in the export are:
- [QR code](https://en.wikipedia.org/wiki/QR_code) with encapsulated data:
- URL with `otpauth-migration://offline?data=`, where data contains:
- [URL encoding](https://en.wikipedia.org/wiki/Percent-encoding)
- [Base64](https://en.wikipedia.org/wiki/Base64)
- [Protocol Buffers](https://en.wikipedia.org/wiki/Protocol_Buffers) serialized data

## Protocol Buffers

A reconstructed definition of the protobuf file is [included in the repo](OtpMigration.proto).

## Bash example

With some regular bash tools and [protoc](https://developers.google.com/protocol-buffers/docs/downloads) you can extract the data like this:

```
$ function urldecode() { : "${*//+/ }"; echo -e "${_//%/\\x}"; }
$ urldecode '<DATA VALUE>' | base64 -d | protoc --decode_raw

1 {
  1: "\r\037)\335\260l\377\216=\0352O+\352\221.o\177\014e\030\217\352NM~V\322\322 \320\351@\314C"
  2: "Demo Issuer:Demo Account"
  4: 1
  5: 1
  6: 2
}
2: 1
3: 1
4: 0
5: 1045125660
```

Note however that this is just raw decoding the protoc buffer and will show field IDs without assigning names. You'll have to lookup the meaning of each field in the [Format description](#format-description).

Alternatively use the provided OtpMigration.proto and instruct `protoc` to decode a `MigrationPayload`:
```
$ urldecode '<DATA VALUE>' | base64 -d | protoc --decode=MigrationPayload OtpMigration.proto

otp_parameters {
  secret: "\r\037)\335\260l\377\216=\0352O+\352\221.o\177\014e\030\217\352NM~V\322\322 \320\351@\314C"
  name: "Demo Issuer:Demo Account"
  algorithm: SHA1
  digits: SIX
  type: TOTP
}
version: 1
batch_size: 1
batch_index: 0
batch_id: 1045125660

```

## Python example

[parse.py](parse.py) contains a sample python script that parses an otpauth-migration URL. The [OtpMigration_pb2.py](OtpMigration_pb2.py) is generated with `protoc --python_out=. OtpMigration.proto`.

```
$ pip install -r requirements.txt
$ ./parse.py '<OTP URL>'

version: 1
batch_size: 1
batch_index: 0
batch_id: 1045125660
otp_parameters:
  secret: b'BUPSTXNQNT7Y4PI5GJHSX2URFZXX6DDFDCH6UTSNPZLNFURA2DUUBTCD'
  name: Demo Issuer:Demo Account
  issuer: 
  algorithm: SHA1
  digits: SIX
  type: TOTP
  counter: 0
```

## Python sample 2 - export to yubikey

Another sample I've included is [export2yubikey.py](export2yubikey.py). This script generates [ykman](https://developers.yubico.com/yubikey-manager/) commands to import the secrets into a yubikey.

```
$ ./export2yubikey.py '<OTP URL>'
ykman oath add -o TOTP -d 6 -s SHA1 -p 30 "example1" INWGK5TFOIQFS33VEFBHK5BAJZXSAU3FMNZGK5A=
ykman oath add -o TOTP -d 6 -s SHA1 -p 30 -i "some issuer" "example2" KN2G64BANF2CCTTPORUGS3THEBUGK4TF
...
```

## Format description

See [OtpMigration.proto](OtpMigration.proto).

### MigrationPayload

**message**

| ID | Name           | Type                            |
|----|----------------|---------------------------------|
| 1  | otp_parameters | [OtpParameters](#otpparameters) |
| 2  | version        | int32                           |
| 3  | batch_size     | int32                           |
| 4  | batch_index    | int32                           |
| 5  | batch_id       | int32                           |

### OtpParameters

**message**

| ID | Name      | Type                      |
|----|-----------|---------------------------
| 1  | secret    | bytes                     |
| 2  | name      | string                    |
| 3  | issuer    | string                    |
| 4  | algorithm | [Algorithm](#algorithm)   |
| 5  | digits    | [DigitCount](#digitcount) |
| 6  | type      | [OtpType](#otptype)       |
| 7  | counter   | int64                     |

### Algorithm

**enum**

| Value | Name                       |
|-------|----------------------------|
| 0     | ALGORITHM_TYPE_UNSPECIFIED |
| 1     | SHA1                       |
| 2     | SHA256                     |
| 3     | SHA512                     |
| 4     | MD5                        |

### DigitCount

**enum**

| Value | Name                    |
|-------|-------------------------|
| 0     | DIGIT_COUNT_UNSPECIFIED |
| 1     | SIX                     |
| 2     | EIGHT                   |

### OtpType

**enum**

| Value | Name                 |
|-------|----------------------|
| 0     | OTP_TYPE_UNSPECIFIED |
| 1     | HOTP                 |
| 2     | TOTP                 |
