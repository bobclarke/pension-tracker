PRAGMA foreign_keys=OFF;
BEGIN TRANSACTION;

CREATE TABLE IF NOT EXISTS "funds"(
"fund name" TEXT, "units held" TEXT, "unit price" TEXT, "Provider" TEXT,
 "Employer" TEXT, "ISIN" TEXT, "Purchased"	TEXT);
INSERT INTO funds VALUES('Example Fund','100.000','100.0','Exmaple Provider','Exmaple Employer','GB00B4W9CK61',NULL);

CREATE TABLE fund_growth (timestamp TEXT, fund TEXT, isin TEXT, value REAL, provider TEXT,  unique(timestamp,isin,provider));
INSERT INTO fund_growth VALUES('2024-04-22','Example','GB00B4W9CK61',100.000,'Example Provider');

CREATE TABLE summary (timestamp TEXT, value REAL, unique(timestamp,value));
INSERT INTO summary VALUES('2024-04-01',100.0);

CREATE UNIQUE INDEX funds_unique_index ON funds(isin,provider);
COMMIT;
