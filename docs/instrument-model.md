# Instrument and listing model

An exchange has an Atlas UUID, MIC, name, optional acronym, country, IANA timezone, currency,
market type, and status. MIC is unique where available.

An instrument has an immutable UUID, names, optional description, asset class, primary currency,
optional country and legitimate identifiers, status, and metadata version. ISIN, CUSIP, SEDOL,
and FIGI are nullable and never fabricated. Supported catalogue classes are equity,
exchange-traded fund, index, foreign exchange, cryptocurrency, commodity, bond, fund, and other.
Legacy Milestone 1 values remain readable.

A listing connects one instrument to one exchange. Venue plus symbol is unique, so identical
symbols across venues and multiple listings per instrument are supported. Currency, status,
primary flag, dates, and decimal tick size belong to the listing.

Legacy `canonical_symbol` and `venue_mic` remain for compatibility but are not identity
boundaries. New code uses Atlas UUIDs and exchange foreign keys. Provider mappings are unique
inside vendor namespaces. Quote and candle constraints reject negative values, malformed shapes,
and duplicate observation periods.
