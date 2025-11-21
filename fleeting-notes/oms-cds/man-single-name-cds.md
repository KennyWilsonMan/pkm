# Man Single Name CDS


## Extracted Information
### Ticket Details 

Book IDs: 137878, 138462, 139750, 143434, 143479
Security ID: 24031746

Here are the extracted details from the OTC CDS on Single Name Ticket:

  Trade Header

  Description: CDS WORLDLINE 500(20-DEC-2026) GOLDMAN SACHS INTERNATIONAL 1,102.86bps

  Static Details

  Reference Entity Information

  - Is SRO: No
  - Ref Entity: WORLDLINE
  - Red Id: FOHED0
  - Ref Obligation: WLNFP 0 7/8 06/30/27 EMTN
  - Credit Curve Code: WORLDLAA-SnrFor:MM1
  - ISIN: FR0013521564

  Contract Terms

  - Currency: EUR
  - SEF Exchange: (blank)
  - Quote Type: Spread
  - Coupon Rate (bp): 500
  - All-In Spread (bp): 1,102.86
  - Credit Events: 3 items selected
  - Coupon Frequency: Quarterly
  - Seniority: Senior
  - Roll Convention: Foll (Following)
  - Doc Clause: MM14
  - Day Count: Act/360
  - Legal Doc Type: DTCC Eligible

  Dates

  - First Accrual Date: 22/09/2025
  - First Coupon Date: 20/12/2025
  - Maturity Term: 1Y
  - Maturity Date: 20/12/2026

  Business Day Centres

  - 2 items selected
  - NY if NA/LATAM/Asia & Tokyo if Japan (NOT...)

  Pricing/Analytics

  - CDS Spread: 1,102.86
  - As of Date: (not populated)
  - Underlying Price: (not populated)
  - Stock Borrow: (not populated)



## OMS DB
First lets look at the CDS Security. 

### CDS Security
```sql
select 
	S.SECURITY_NAME,
	SC.SECURITY_CLASS_NAME,
	PC.BOOKED_OPEN_QUANTITY, 
	PC.BOOKED_QUANTITY,
	S.ISSUER_ID
from 
	Inventory.POSITION_CORE PC
inner join 
	Inventory.[SECURITY] S ON S.SECURITY_ID = PC.SECURITY_ID
inner join 
	Inventory.SECURITY_CLASS SC ON SC.SECURITY_CLASS_ID = S.SECURITY_CLASS_ID
where 
	PC.SECURITY_ID = 24031746
and
	PC.BOOK_ID = 137878

```

Here's the data converted to markdown in transposed form:

| Field | Value |
|-------|-------|
| **SECURITY_NAME** | CDS WORLDLINE 500(20-DEC-2026) GOLDMAN SACHS INTE... |
| **SECURITY_CLASS_NAME** | Credit Default Swap |
| **BOOKED_OPEN_QUANTITY** | 568800.00000000 |
| **BOOKED_QUANTITY** | 568800.00000000 |
| **ISSUER_ID** | 2690900 |

### Reference Entity / Issuer / RED CODE
```sql
select 
	I.ISSUER_NAME, 
	I.LEGAL_ENTITY_ID,
	LE.LEGAL_NAME,
	LE.MARKIT_RED_ENTITY
from 
	Inventory.ISSUER I
inner join 
	Inventory.LEGAL_ENTITY LE ON LE.LEGAL_ENTITY_ID = I.LEGAL_ENTITY_ID
WHERE 
	I.ISSUER_ID = 2690900
```

| Field | Value |
|-------|-------|
| **ISSUER_NAME** | WORLDLINE |
| **LEGAL_ENTITY_ID** | 76807 |
| **LEGAL_NAME** | Worldline |
| **MARKIT_RED_ENTITY** | FOHED0 |

### Reference Obligation
```sql
-- Now lets look at the Reference Obligation
select 
	REF_SEC.SECURITY_NAME,
	REF_SEC_CLASS.SECURITY_CLASS_NAME
from 
	Inventory.SECURITY_FIXED_INCOME SFI
inner join 
	Inventory.[SECURITY] REF_SEC ON REF_SEC.SECURITY_ID = SFI.REFERENCE_OBLIGATION_SECURITY_ID
inner join 
	Inventory.SECURITY_CLASS REF_SEC_CLASS ON REF_SEC_CLASS.SECURITY_CLASS_ID = REF_SEC.SECURITY_CLASS_ID
where 
	SFI.SECURITY_ID = 24031746
```

Here's the data converted to markdown in transposed form:

| Field | Value |
|-------|-------|
| **SECURITY_NAME** | WLNFP 0 7/8 06/30/27 EMTN |
| **SECURITY_CLASS_NAME** | Bond |


