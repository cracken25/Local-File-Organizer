# LocalFileOrganizer Taxonomy

This document defines the complete taxonomy structure for file classification in LocalFileOrganizer. All files must be classified into one of the categories defined below following the KB.Domain.Scope hierarchy.

## Classification Rules

### Single Primary Home Rule

Each document must have ONE primary classification location. If a document fits multiple categories, choose the most specific and relevant category based on the document's primary purpose.

### Confidence Scoring

- **High Confidence (>0.8)**: Clear indicators match the category definition
- **Medium Confidence (0.5-0.8)**: Document fits category but has some ambiguity
- **Low Confidence (<0.5)**: Unclear fit, consider KB.Personal.Misc

---

## KB.Finance - Financial Documents

### KB.Finance.Tax - Tax Related Documents

#### KB.Finance.Tax.Filing - Tax Filing Documents

**Description**: Filed tax returns and supporting documentation

##### KB.Finance.Tax.Filing.Federal

- **Purpose**: Federal tax returns, IRS forms, and federal tax correspondence
- **Examples**: Form 1040, 1099, W-2, IRS letters
- **Quality Test**: Does the document contain IRS forms or federal tax information?

##### KB.Finance.Tax.Filing.State

- **Purpose**: State tax returns and state tax authority correspondence
- **Examples**: State income tax forms, state tax notices
- **Quality Test**: Does the document reference a specific state tax authority?

#### KB.Finance.Tax.Planning - Tax Planning Documents

**Description**: Tax strategy, projections, and planning materials

##### KB.Finance.Tax.Planning.Strategy

- **Purpose**: Tax planning strategies, optimization approaches
- **Examples**: Tax planning memos, strategy documents
- **Quality Test**: Does the document discuss future tax strategies or optimization?

##### KB.Finance.Tax.Planning.Projections

- **Purpose**: Tax liability estimates and projections
- **Examples**: Estimated tax worksheets, projection spreadsheets
- **Quality Test**: Does the document contain forward-looking tax calculations?

#### KB.Finance.Tax.Records - Tax Supporting Records

**Description**: Documentation used to support tax filings

##### KB.Finance.Tax.Records.Receipts

- **Purpose**: Receipts for tax-deductible expenses
- **Examples**: Charitable donation receipts, business expense receipts
- **Quality Test**: Is this a receipt for a potentially deductible item?

##### KB.Finance.Tax.Records.Statements

- **Purpose**: Financial statements used for tax preparation
- **Examples**: Year-end investment statements, mortgage interest statements
- **Quality Test**: Does the document provide tax-relevant financial information?

---

### KB.Finance.Banking - Banking and Cash Management

#### KB.Finance.Banking.Statements

**Description**: Bank account statements and transaction records

##### KB.Finance.Banking.Statements.Checking

- **Purpose**: Checking account statements
- **Examples**: Monthly checking statements, check images
- **Quality Test**: Is this a checking account statement?

##### KB.Finance.Banking.Statements.Savings

- **Purpose**: Savings account statements
- **Examples**: Savings account statements, interest notices
- **Quality Test**: Is this a savings account statement?

#### KB.Finance.Banking.Transactions

**Description**: Individual transaction records and confirmations

##### KB.Finance.Banking.Transactions.Transfers

- **Purpose**: Transfer confirmations between accounts
- **Examples**: Wire transfer receipts, ACH confirmations
- **Quality Test**: Does the document confirm a fund transfer?

##### KB.Finance.Banking.Transactions.Deposits

- **Purpose**: Deposit confirmations and records
- **Examples**: Deposit slips, mobile deposit confirmations
- **Quality Test**: Does the document confirm a deposit?

---

### KB.Finance.Investments - Investment Accounts and Records

#### KB.Finance.Investments.Statements

**Description**: Investment account statements

##### KB.Finance.Investments.Statements.Brokerage

- **Purpose**: Brokerage account statements
- **Examples**: Monthly brokerage statements, trade confirmations
- **Quality Test**: Is this from a brokerage firm showing holdings?

##### KB.Finance.Investments.Statements.Retirement

- **Purpose**: Retirement account statements (401k, IRA, etc.)
- **Examples**: 401k statements, IRA statements
- **Quality Test**: Is this a retirement account statement?

#### KB.Finance.Investments.Performance

**Description**: Investment performance reports and analysis

##### KB.Finance.Investments.Performance.Reports

- **Purpose**: Performance analysis and reports
- **Examples**: Quarterly performance reports, gain/loss statements
- **Quality Test**: Does the document analyze investment performance?

---

### KB.Finance.Insurance - Insurance Policies and Claims

#### KB.Finance.Insurance.Policies

**Description**: Insurance policy documents

##### KB.Finance.Insurance.Policies.Health

- **Purpose**: Health insurance policies and documentation
- **Examples**: Health insurance cards, policy documents, coverage summaries
- **Quality Test**: Is this health insurance documentation?

##### KB.Finance.Insurance.Policies.Auto

- **Purpose**: Auto insurance policies
- **Examples**: Auto insurance policies, insurance ID cards
- **Quality Test**: Is this auto insurance documentation?

##### KB.Finance.Insurance.Policies.Home

- **Purpose**: Home/renters insurance policies
- **Examples**: Homeowners insurance, renters insurance policies
- **Quality Test**: Is this property insurance documentation?

##### KB.Finance.Insurance.Policies.Life

- **Purpose**: Life insurance policies
- **Examples**: Life insurance policies, beneficiary designations
- **Quality Test**: Is this life insurance documentation?

#### KB.Finance.Insurance.Claims

**Description**: Insurance claims and related correspondence

##### KB.Finance.Insurance.Claims.Filed

- **Purpose**: Filed insurance claims
- **Examples**: Claim forms, claim receipts
- **Quality Test**: Is this a filed insurance claim?

##### KB.Finance.Insurance.Claims.Settled

- **Purpose**: Settled insurance claims and documentation
- **Examples**: Settlement letters, payment confirmations
- **Quality Test**: Does this document show claim settlement?

---

### KB.Finance.Loans - Loans and Credit

#### KB.Finance.Loans.Mortgage

**Description**: Mortgage documentation

##### KB.Finance.Loans.Mortgage.Documents

- **Purpose**: Mortgage agreements and closing documents
- **Examples**: Mortgage notes, closing disclosures
- **Quality Test**: Is this mortgage closing documentation?

##### KB.Finance.Loans.Mortgage.Statements

- **Purpose**: Monthly mortgage statements
- **Examples**: Monthly mortgage statements, escrow statements
- **Quality Test**: Is this a mortgage payment statement?

#### KB.Finance.Loans.Credit

**Description**: Credit cards and lines of credit

##### KB.Finance.Loans.Credit.Statements

- **Purpose**: Credit card statements
- **Examples**: Monthly credit card statements
- **Quality Test**: Is this a credit card statement?

##### KB.Finance.Loans.Credit.Agreements

- **Purpose**: Credit agreements and terms
- **Examples**: Credit card agreements, terms and conditions
- **Quality Test**: Is this a credit agreement document?

---

## KB.Personal - Personal Documents

### KB.Personal.Identity - Identity Documents

#### KB.Personal.Identity.Government

**Description**: Government-issued identity documents

##### KB.Personal.Identity.Government.Passport

- **Purpose**: Passport documents and applications
- **Examples**: Passport copies, passport applications
- **Quality Test**: Is this passport-related?

##### KB.Personal.Identity.Government.License

- **Purpose**: Driver's licenses and state IDs
- **Examples**: Driver's license copies, state ID cards
- **Quality Test**: Is this a driver's license or state ID?

##### KB.Personal.Identity.Government.SSN

- **Purpose**: Social Security documentation
- **Examples**: Social Security cards, SSN verification
- **Quality Test**: Does this relate to Social Security?

#### KB.Personal.Identity.Certificates

**Description**: Birth certificates, marriage certificates, etc.

##### KB.Personal.Identity.Certificates.Birth

- **Purpose**: Birth certificates
- **Examples**: Birth certificate copies
- **Quality Test**: Is this a birth certificate?

##### KB.Personal.Identity.Certificates.Marriage

- **Purpose**: Marriage certificates and licenses
- **Examples**: Marriage licenses, marriage certificates
- **Quality Test**: Is this marriage documentation?

---

### KB.Personal.Health - Health and Medical Records

#### KB.Personal.Health.Records

**Description**: Medical records and test results

##### KB.Personal.Health.Records.Visits

- **Purpose**: Doctor visit summaries and notes
- **Examples**: Visit summaries, doctor notes
- **Quality Test**: Is this from a medical visit?

##### KB.Personal.Health.Records.Labs

- **Purpose**: Lab results and diagnostic tests
- **Examples**: Blood test results, imaging reports
- **Quality Test**: Are these lab or test results?

#### KB.Personal.Health.Prescriptions

**Description**: Prescription records

##### KB.Personal.Health.Prescriptions.Current

- **Purpose**: Current prescription information
- **Examples**: Current prescription lists, prescription labels
- **Quality Test**: Is this current prescription information?

---

### KB.Personal.Education - Educational Records

#### KB.Personal.Education.Transcripts

**Description**: Academic transcripts

##### KB.Personal.Education.Transcripts.Undergraduate

- **Purpose**: Undergraduate transcripts
- **Examples**: College transcripts
- **Quality Test**: Is this an undergraduate transcript?

##### KB.Personal.Education.Transcripts.Graduate

- **Purpose**: Graduate school transcripts
- **Examples**: Master's, PhD transcripts
- **Quality Test**: Is this a graduate transcript?

#### KB.Personal.Education.Certifications

**Description**: Professional certifications and licenses

##### KB.Personal.Education.Certifications.Professional

- **Purpose**: Professional certifications
- **Examples**: CPA certificates, professional licenses
- **Quality Test**: Is this a professional certification?

---

### KB.Personal.Misc - Miscellaneous Personal Files

**Description**: Personal files that don't fit clearly into other categories

**Purpose**: Catch-all for personal documents that don't have a clear primary home

**Quality Test**: Does this document not fit clearly into any other defined category?

---

## KB.Work - Work and Employment Documents

### KB.Work.Employment - Employment Records

#### KB.Work.Employment.Contracts

**Description**: Employment contracts and agreements

##### KB.Work.Employment.Contracts.Current

- **Purpose**: Current employment contracts
- **Examples**: Current offer letters, employment agreements
- **Quality Test**: Is this a current employment contract?

##### KB.Work.Employment.Contracts.Past

- **Purpose**: Past employment contracts
- **Examples**: Previous employment agreements
- **Quality Test**: Is this from a previous employer?

#### KB.Work.Employment.Compensation

**Description**: Compensation documentation

##### KB.Work.Employment.Compensation.Paystubs

- **Purpose**: Pay stubs and payment records
- **Examples**: Bi-weekly paystubs, direct deposit confirmations
- **Quality Test**: Is this a pay stub or payment record?

##### KB.Work.Employment.Compensation.Benefits

- **Purpose**: Benefits documentation
- **Examples**: Benefits enrollment, benefits summaries
- **Quality Test**: Does this document employee benefits?

---

### KB.Work.Projects - Work Projects and Deliverables

#### KB.Work.Projects.Active

**Description**: Currently active work projects

##### KB.Work.Projects.Active.Documents

- **Purpose**: Active project documents and deliverables
- **Examples**: Project plans, status reports
- **Quality Test**: Is this for an active work project?

#### KB.Work.Projects.Archive

**Description**: Completed or archived projects

##### KB.Work.Projects.Archive.Documents

- **Purpose**: Archived project documentation
- **Examples**: Completed project final reports
- **Quality Test**: Is this from a completed project?

---

## KB.Legal - Legal Documents

### KB.Legal.Contracts - Legal Contracts

#### KB.Legal.Contracts.Real Estate

**Description**: Real estate contracts and agreements

##### KB.Legal.Contracts.RealEstate.Purchase

- **Purpose**: Property purchase agreements
- **Examples**: Home purchase contracts, addendums
- **Quality Test**: Is this a property purchase contract?

##### KB.Legal.Contracts.RealEstate.Lease

- **Purpose**: Lease and rental agreements
- **Examples**: Apartment leases, rental agreements
- **Quality Test**: Is this a lease or rental agreement?

---

### KB.Legal.Estate - Estate Planning

#### KB.Legal.Estate.Planning

**Description**: Wills, trusts, and estate planning documents

##### KB.Legal.Estate.Planning.Will

- **Purpose**: Last will and testament
- **Examples**: Will documents, will updates
- **Quality Test**: Is this a will document?

##### KB.Legal.Estate.Planning.Trust

- **Purpose**: Trust documents
- **Examples**: Living trusts, trust agreements
- **Quality Test**: Is this a trust document?

##### KB.Legal.Estate.Planning.POA

- **Purpose**: Power of Attorney documents
- **Examples**: Healthcare POA, financial POA
- **Quality Test**: Is this a Power of Attorney document?

---

## Classification Guidelines

### When Multiple Categories Apply

If a document could fit multiple categories:

1. Choose the **most specific** category
2. Prioritize the document's **primary purpose**
3. Consider the **most likely retrieval context**

### Examples

- **Tax-related investment statement** → KB.Finance.Tax.Records.Statements (tax context is primary)
- **Health insurance EOB** → KB.Finance.Insurance.Claims.Settled (insurance claim context, not health record)
- **W-2 form** → KB.Finance.Tax.Records.Statements (tax supporting document)

### Confidence Thresholds

- **>0.9**: Document clearly matches all criteria
- **0.7-0.9**: Document matches most criteria with minor ambiguities
- **0.5-0.7**: Document fits category but requires judgment
- **<0.5**: Poor fit, consider KB.Personal.Misc or request human review
