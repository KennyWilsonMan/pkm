# Security Envoy and OMS DB

[← Back to OMS CDS Notes](./README.md)

This document describes how to setup a CDS using the Rosa Security Envoy and then view the results of the created security on the OMS Database. 

## Security Envoy
There are two end points on the security envoy: one for creating CDS on single names and one for creating CDS on an index.

### Create CDS on Single Name

https://rosa-securityenvoy-n1-dev.maninvestments.ad.man.com:8374/swagger/index.html#/GenericSecurity/GenericSecurity_GetOrCreateCdsOnSingleName

```json
{
  "currencyId": 31,
  "maturityDate": "2030-12-20",
  "couponRate": 0.05,
  "redCode": "687DNGAA9",
  "docClause": "XR14"
}
```

### Create CDS on Index
https://rosa-securityenvoy-n1-dev.maninvestments.ad.man.com:8374/swagger/index.html#/GenericSecurity/GenericSecurity_GetOrCreateCdsIndex

```json
{
  "currencyId": 31,
  "maturityDate": "2030-12-20",
  "redCode": "2I65BYDY8",
  "term": 26
}

```


## OMS DB

### CDS on Single Name




