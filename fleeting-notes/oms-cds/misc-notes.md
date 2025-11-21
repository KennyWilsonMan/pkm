# Misc Notes

[← Back to OMS CDS Notes](./README.md)

### Amending existing positions from Panorama 

We can reduce or unwind existing position in four ways; two for Bilareral OTC and two for Clearing House based trades.

**Bilateral**
* **UNWIND** Trade with the same counterparty the initial trade was with 
* **ASSIGNMENT** - Trade with (Novate to)  a 3rd counterparty which us as the original counterparty agree with. Perhaps free form instructions

**Cleared Trades**

* **OFFSET** Opposing trade but not against original security. It creates a new security 
* **CLOSE OUT** Unwinding the original position in the same security

