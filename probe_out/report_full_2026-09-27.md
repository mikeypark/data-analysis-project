# 후보 데이터 실물 확인 리포트

실행 2026-09-27 - pandas 2.3.3 - python 3.13.15

이 리포트는 문서상 스펙과 실제 데이터가 일치하는지 대조하기 위한 것입니다.

---

## 후보 A - SEC Form 13F

발견한 분기 파일 54개. 아래 3개를 받습니다.

| 분기 | URL |
|---|---|
| 2023q4 | `https://www.sec.gov/files/structureddata/data/form-13f-data-sets/2023q4_form13f.zip` |
| 2023q3 | `https://www.sec.gov/files/structureddata/data/form-13f-data-sets/2023q3_form13f.zip` |
| 2022q3 | `https://www.sec.gov/files/structureddata/data/form-13f-data-sets/2022q3_form13f.zip` |

**2023q4** - zip 내부 파일: `COVERPAGE.tsv`, `INFOTABLE.tsv`, `OTHERMANAGER.tsv`, `OTHERMANAGER2.tsv`, `SIGNATURE.tsv`, `SUBMISSION.tsv`, `SUMMARYPAGE.tsv`, `FORM13F_metadata.json`, `FORM13F_readme.htm`

### `sec_2023q4_INFOTABLE`

보유 종목 명세. 이 프로젝트의 본체 테이블입니다.

- 행 2,886,468 / 열 15
- 메모리 2,147.7 MB

| 컬럼 | dtype | 결측 | 고유값 | 범위 |
|---|---|---:|---:|---|
| `ACCESSION_NUMBER` | object | 0.0% | 7,519 | 0000004977-23-0001 ~ 0002004581-23-0000 |
| `INFOTABLE_SK` | object | 0.0% | 2,886,468 | 83875535 ~ 95332730 |
| `NAMEOFISSUER` | object | 0.0% | 147,084 |  10X CAPITAL VENTU ~ xxx |
| `TITLEOFCLASS` | object | 0.0% | 21,206 |        COM ~ yum |
| `CUSIP` | object | 0.0% | 35,442 | 000000000 ~ y9390m103 |
| `FIGI` | object | 92.8% | 15,163 | 000000000000 ~ XXXXXXXXXXXX |
| `VALUE` | object | 0.0% | 1,421,752 | 0 ~ 9999999 |
| `SSHPRNAMT` | object | 0.0% | 439,567 | 0 ~ 99999999 |
| `SSHPRNAMTTYPE` | object | 0.0% | 2 | PRN ~ SH |
| `PUTCALL` | object | 95.2% | 2 | Call ~ Put |
| `INVESTMENTDISCRETION` | object | 0.0% | 3 | DFND ~ SOLE |
| `OTHERMANAGER` | object | 56.5% | 1,722 | ,14 ~ none |
| `VOTING_AUTH_SOLE` | object | 0.0% | 352,406 | 0 ~ 99999999 |
| `VOTING_AUTH_SHARED` | object | 0.0% | 93,265 | 0 ~ 99999 |
| `VOTING_AUTH_NONE` | object | 0.0% | 187,977 | 0 ~ 99997 |

샘플 200행 → `samples/sec_2023q4_INFOTABLE.csv`

### `sec_2023q4_SUBMISSION`

`FILING_DATE` 와 `PERIODOFREPORT` 가 여기 있습니다. 45일 지연을 다루려면 이 두 컬럼이 핵심입니다.

- 행 9,196 / 열 5
- 메모리 2.7 MB

| 컬럼 | dtype | 결측 | 고유값 | 범위 |
|---|---|---:|---:|---|
| `ACCESSION_NUMBER` | object | 0.0% | 9,196 | 0000004977-23-0001 ~ 0002004581-23-0000 |
| `FILING_DATE` | object | 0.0% | 58 | 01-DEC-2023 ~ 31-OCT-2023 |
| `SUBMISSIONTYPE` | object | 0.0% | 4 | 13F-HR ~ 13F-NT/A |
| `CIK` | object | 0.0% | 8,603 | 0000002230 ~ 1891834 |
| `PERIODOFREPORT` | object | 0.0% | 31 | 30-JUN-2016 ~ 31-MAR-2023 |

샘플 200행 → `samples/sec_2023q4_SUBMISSION.csv`

### `sec_2023q4_COVERPAGE`

`FILINGMANAGER_NAME` - 운용사 이름.

- 행 9,196 / 열 21
- 메모리 9.1 MB

| 컬럼 | dtype | 결측 | 고유값 | 범위 |
|---|---|---:|---:|---|
| `ACCESSION_NUMBER` | object | 0.0% | 9,196 | 0000004977-23-0001 ~ 0002004581-23-0000 |
| `REPORTCALENDARORQUARTER` | object | 0.0% | 31 | 30-JUN-2016 ~ 31-MAR-2023 |
| `ISAMENDMENT` | object | 43.1% | 2 | N ~ Y |
| `AMENDMENTNO` | object | 96.6% | 6 | 1 ~ 6 |
| `AMENDMENTTYPE` | object | 96.6% | 2 | NEW HOLDINGS ~ RESTATEMENT |
| `CONFDENIEDEXPIRED` | object | 98.9% | 2 | N ~ Y |
| `DATEDENIEDEXPIRED` | object | 99.7% | 7 | 13-NOV-2023 ~ 30-SEP-2023 |
| `DATEREPORTED` | object | 99.7% | 11 | 14-AUG-2023 ~ 31-MAR-2023 |
| `REASONFORNONCONFIDENTIALITY` | object | 99.7% | 1 | Confidential Treat ~ Confidential Treat |
| `FILINGMANAGER_NAME` | object | 0.0% | 8,604 | &PARTNERS ~ venBio Partners LL |
| `FILINGMANAGER_STREET1` | object | 0.0% | 7,362 | #04-01B, DELTA HOU ~ c/o Wellington Man |
| `FILINGMANAGER_STREET2` | object | 44.5% | 2,224 | # 15-02 MILLENIA T ~ ZHONGSHAN N RD, ZH |
| `FILINGMANAGER_CITY` | object | 0.1% | 1,917 | - ~ Zurich |
| `FILINGMANAGER_STATEORCOUNTRY` | object | 0.0% | 110 | 2M ~ Z4 |
| `FILINGMANAGER_ZIPCODE` | object | 0.2% | 3,175 | - ~ XXXXX |
| `REPORTTYPE` | object | 0.0% | 3 | 13F COMBINATION RE ~ 13F NOTICE |
| `FORM13FFILENUMBER` | object | 0.0% | 8,603 | 028-00030 ~ 028-23480 |
| `CRDNUMBER` | object | 57.6% | 3,564 | 000000000 ~ 080132688 |
| `SECFILENUMBER` | object | 59.5% | 3,388 | 000-15071 ~ 867-01256 |
| `PROVIDEINFOFORINSTRUCTION5` | object | 0.0% | 2 | N ~ Y |
| `ADDITIONALINFORMATION` | object | 95.5% | 321 | (1) A power of att ~ Yorktown XI Compan |

샘플 200행 → `samples/sec_2023q4_COVERPAGE.csv`

**2023q3** - zip 내부 파일: `COVERPAGE.tsv`, `INFOTABLE.tsv`, `OTHERMANAGER.tsv`, `OTHERMANAGER2.tsv`, `SIGNATURE.tsv`, `SUBMISSION.tsv`, `SUMMARYPAGE.tsv`, `FORM13F_metadata.json`, `FORM13F_readme.htm`

**2022q3** - zip 내부 파일: `COVERPAGE.tsv`, `INFOTABLE.tsv`, `OTHERMANAGER.tsv`, `OTHERMANAGER2.tsv`, `SIGNATURE.tsv`, `SUBMISSION.tsv`, `SUMMARYPAGE.tsv`, `FORM13F_metadata.json`, `FORM13F_readme.htm`

### 검증 1 - 45일 공시 지연이 실제로 있는가

2023q4 제출 9,196건의 `FILING_DATE - PERIODOFREPORT` (일):

| 통계 | 일수 |
|---|---:|
| 최소 | 2 |
| 25% | 30 |
| 중앙값 | 44 |
| 75% | 45 |
| 최대 | 2,776 |

45일 넘겨 제출된 건: **9.0%**

> 중앙값이 40일대라면 45일 규칙이 데이터에서 확인된 것입니다. `PERIODOFREPORT` 를 분석 시점으로 쓰면 이만큼의 미래 정보를 쓰게 됩니다.

### 검증 2 - VALUE 단위 (천달러 vs 달러)

`VALUE / SSHPRNAMT` 는 주당 단가입니다. 단위가 천달러면 이 값이 비정상적으로 작게 나옵니다.

| 분기 | 중앙 단가 | 판정 |
|---|---:|---|
| 2023q4 | 47.5599 | 달러 단위로 보입니다 |
| 2023q3 | 46.0400 | 달러 단위로 보입니다 |
| 2022q3 | 0.0542 | **천달러 단위로 보입니다** |

> 2023년 1월 3일 전후 분기를 같이 받으면 이 표에서 1000배 차이가 눈에 보입니다. 이게 2차 산출물의 '데이터 품질 확인' 절 첫 번째 항목이 됩니다.

---

## 후보 B - KRX 투자자별 거래실적

요청 구간: `20230925` ~ `20260924` (T+2 지연을 감안해 3일 전까지)

**시장 전체 조회 실패** - `KeyError('거래대금')`
> 스크래퍼가 깨졌을 가능성이 있습니다. 후보 B의 재현성 리스크가 바로 이것입니다.

### `krx_005930_daily_by_investor`

삼성전자(005930) 일별 투자자별 순매수. 시계열 분석의 최소 단위입니다.

- 행 0 / 열 1
- 메모리 0.0 MB

| 컬럼 | dtype | 결측 | 고유값 | 범위 |
|---|---|---:|---:|---|
| `index` | int64 | nan% | 0 |  |

샘플 200행 → `samples/krx_005930_daily_by_investor.csv`

### `krx_005930_ohlcv`

삼성전자 일별 시세. 순매수와 붙여 성과를 봅니다.

- 행 728 / 열 7
- 메모리 0.0 MB

| 컬럼 | dtype | 결측 | 고유값 | 범위 |
|---|---|---:|---:|---|
| `날짜` | datetime64[ns] | 0.0% | 728 | 2023-09-25 ~ 2026-09-23 |
| `시가` | int64 | 0.0% | 450 | 5.02e+04 ~ 3.725e+05 |
| `고가` | int64 | 0.0% | 441 | 5.14e+04 ~ 3.745e+05 |
| `저가` | int64 | 0.0% | 444 | 4.99e+04 ~ 3.52e+05 |
| `종가` | int64 | 0.0% | 450 | 4.99e+04 ~ 3.625e+05 |
| `거래량` | int64 | 0.0% | 728 | 5.848e+06 ~ 8.943e+07 |
| `등락률` | float64 | 0.0% | 679 | -13.39 ~ 26.81 |

샘플 200행 → `samples/krx_005930_ohlcv.csv`

---

> 주의 - 이 파일은 `probe_data.py` 의 첫 실행(다운로드 + 품질 점검) 결과를 보존한 사본입니다.
> 이후 `--list` 실행이 `report.md` 를 덮어썼기 때문에 별도 이름으로 남깁니다.
>
> 또한 위 표의 "범위" 칸은 `object` 타입 컬럼에 대해 문자열로 비교한 값입니다.
> 예를 들어 `FILING_DATE` 의 `01-DEC-2023 ~ 31-OCT-2023` 은 날짜 범위가 아니라 문자열 정렬 결과이며,
> 실제 파싱하면 2023-10-30 ~ 2023-12-01 입니다.
