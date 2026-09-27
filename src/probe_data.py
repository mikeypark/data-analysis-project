# /// script
# requires-python = ">=3.11"
# dependencies = ["pandas>=2.2", "requests>=2.31", "pykrx>=1.0.45"]
# ///
"""
데이터분석 프로젝트 - 후보 데이터 실물 확인 스크립트

실행:
    uv run probe_data.py                 # 후보 A, B 모두
    uv run probe_data.py --only sec      # SEC 13F 만
    uv run probe_data.py --only krx      # KRX 만
    uv run probe_data.py --quarters 4    # 최근 분기 수 (기본 2)
    uv run probe_data.py --also ""       # 단위 전환 비교용 과거 분기 안 받기
    uv run probe_data.py --only sec --list   # 다운로드 없이 분기 목록만 (몇 초)

만들어지는 것 (스크립트와 같은 폴더의 probe_out/):
    report.md          <- 사람이 읽는 품질 리포트
    samples/*.csv      <- 각 데이터 앞 200행 (Claude 가 읽을 용)
    raw/               <- 내려받은 원본 (용량 큼, GitHub 에 올리지 말 것)

이메일은 SEC 가 요구하는 User-Agent 용입니다. 바꾸셔도 됩니다.
"""

from __future__ import annotations

import argparse
import io
import re
import sys
import zipfile
from datetime import date, timedelta
from pathlib import Path

import pandas as pd
import requests

CONTACT = "zoospark@gmail.com"
UA = f"SNU data-analysis coursework ({CONTACT})"

OUT = Path(__file__).resolve().parent / "probe_out"
RAW = OUT / "raw"
SAMPLES = OUT / "samples"

SEC_INDEX = "https://www.sec.gov/data-research/sec-markets-data/form-13f-data-sets"

# 보고서를 메모리에 모아 마지막에 UTF-8 로 한 번에 씁니다.
# (윈도우 콘솔 인코딩 때문에 한글을 바로 print 하면 깨질 수 있어서)
LINES: list[str] = []


def say(line: str = "") -> None:
    LINES.append(line)


def log(msg: str) -> None:
    """진행 상황만 콘솔에. 인코딩 사고를 피하려고 ascii 로 흘립니다."""
    sys.stdout.write(msg.encode("ascii", "replace").decode("ascii") + "\n")
    sys.stdout.flush()


# -------------------------------------------------------------- 품질 프로파일


def profile(df: pd.DataFrame, name: str, note: str = "") -> None:
    """한 테이블의 품질을 리포트에 적고, 앞 200행을 샘플로 저장."""
    say(f"### `{name}`")
    say()
    if note:
        say(note)
        say()
    say(f"- 행 {len(df):,} / 열 {len(df.columns)}")
    mem = df.memory_usage(deep=True).sum() / 1024**2
    say(f"- 메모리 {mem:,.1f} MB")
    say()

    rows = []
    for col in df.columns:
        s = df[col]
        null_pct = s.isna().mean() * 100
        try:
            nuniq = f"{s.nunique(dropna=True):,}"
        except TypeError:
            nuniq = "-"
        rng = ""
        if pd.api.types.is_numeric_dtype(s) and s.notna().any():
            rng = f"{s.min():,.4g} ~ {s.max():,.4g}"
        elif pd.api.types.is_datetime64_any_dtype(s) and s.notna().any():
            rng = f"{s.min():%Y-%m-%d} ~ {s.max():%Y-%m-%d}"
        else:
            vals = s.dropna().astype(str)
            if len(vals):
                rng = f"{vals.min()[:18]} ~ {vals.max()[:18]}"
        rows.append((col, str(s.dtype), f"{null_pct:.1f}%", nuniq, rng))

    say("| 컬럼 | dtype | 결측 | 고유값 | 범위 |")
    say("|---|---|---:|---:|---|")
    for r in rows:
        say("| `{}` | {} | {} | {} | {} |".format(*r))
    say()

    SAMPLES.mkdir(parents=True, exist_ok=True)
    path = SAMPLES / f"{name}.csv"
    df.head(200).to_csv(path, index=False, encoding="utf-8-sig")
    say(f"샘플 200행 → `samples/{name}.csv`")
    say()


# -------------------------------------------------------------- 후보 A: SEC 13F


_MON = {m: i + 1 for i, m in enumerate(
    ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"])}


def label_of(href: str) -> tuple[str, tuple[int, int]]:
    """파일명에서 (라벨, 정렬키=(연, 분기)) 를 뽑습니다.

    SEC 는 분기 파일 이름을 한 가지로만 쓰지 않습니다. `2023q4_form13f.zip` 인 것도 있고
    `01jan2024-31mar2024_form13f.zip` 처럼 날짜 구간으로 쓴 것도 있어서 둘 다 받습니다.
    문자열로 정렬하면 `01jan2024...` 가 `2023q4` 보다 작게 나와 최신 분기를 놓칩니다.
    """
    stem = Path(href).stem
    m = re.search(r"(\d{4})\s*[qQ]\s*([1-4])", stem)
    if m:
        y, q = int(m.group(1)), int(m.group(2))
        return f"{y}q{q}", (y, q)

    m = re.search(r"(\d{1,2})([a-z]{3})(\d{4})", stem, re.I)
    if m and m.group(2).lower() in _MON:
        y = int(m.group(3))
        q = (_MON[m.group(2).lower()] - 1) // 3 + 1
        return f"{y}q{q}", (y, q)

    return stem, (0, 0)


def find_sec_zips(session: requests.Session) -> list[tuple[str, str]]:
    """SEC 페이지에서 분기별 13F zip 링크를 찾아 (라벨, URL) 목록으로. 최신순."""
    r = session.get(SEC_INDEX, timeout=60)
    r.raise_for_status()
    html = r.text

    found: dict[str, tuple[str, tuple[int, int]]] = {}
    for m in re.finditer(r'href="([^"]+?\.zip)"', html, re.I):
        href = m.group(1)
        if "13f" not in href.lower():
            continue
        url = href if href.startswith("http") else "https://www.sec.gov" + href
        label, key = label_of(href)
        found.setdefault(label, (url, key))

    ordered = sorted(found.items(), key=lambda kv: kv[1][1], reverse=True)
    return [(label, url) for label, (url, _) in ordered]


def load_13f_table(zf: zipfile.ZipFile, stem: str) -> pd.DataFrame | None:
    """zip 안에서 이름이 stem 인 탭구분 텍스트를 읽습니다."""
    for info in zf.infolist():
        if Path(info.filename).stem.upper() == stem.upper():
            with zf.open(info) as fh:
                return pd.read_csv(
                    fh, sep="\t", dtype=str, encoding="utf-8",
                    on_bad_lines="warn", low_memory=False,
                )
    return None


def probe_sec(quarters: int, also: list[str], list_only: bool = False) -> None:
    say("## 후보 A - SEC Form 13F")
    say()

    session = requests.Session()
    session.headers.update({"User-Agent": UA, "Accept-Encoding": "gzip, deflate"})

    try:
        zips = find_sec_zips(session)
    except Exception as e:
        say(f"**실패** - SEC 목록 페이지를 못 읽었습니다: `{e!r}`")
        say()
        return

    if not zips:
        say("**실패** - 페이지에서 13F zip 링크를 못 찾았습니다. SEC 가 페이지 구조를 바꿨을 수 있습니다.")
        say()
        return

    if list_only:
        say(f"### 받을 수 있는 분기 전체 - {len(zips)}개 (최신순)")
        say()
        say("| # | 분기 | 파일 |")
        say("|---:|---|---|")
        for n, (label, url) in enumerate(zips, 1):
            say(f"| {n} | {label} | `{Path(url).name}` |")
        say()
        log(f"[SEC] {len(zips)} quarters listed: newest={zips[0][0]} oldest={zips[-1][0]}")
        return

    picked = zips[:quarters]
    picked_labels = {lb for lb, _ in picked}
    for want in also:
        for lb, url in zips:
            if lb.lower() == want.lower() and lb not in picked_labels:
                picked.append((lb, url))
                picked_labels.add(lb)
                break
        else:
            say(f"> `{want}` 는 목록에 없어 건너뜁니다.")
            say()

    first_label = picked[0][0] if picked else None

    say(f"발견한 분기 파일 {len(zips)}개. 아래 {len(picked)}개를 받습니다.")
    say()
    say("| 분기 | URL |")
    say("|---|---|")
    for label, url in picked:
        say(f"| {label} | `{url}` |")
    say()

    RAW.mkdir(parents=True, exist_ok=True)
    infotables: dict[str, pd.DataFrame] = {}

    for label, url in picked:
        dest = RAW / f"{label}_form13f.zip"
        try:
            if dest.exists() and dest.stat().st_size > 0:
                log(f"[SEC] {label} cached ({dest.stat().st_size/1024**2:.0f} MB)")
                blob = dest.read_bytes()
            else:
                log(f"[SEC] downloading {label} ...")
                resp = session.get(url, timeout=600)
                resp.raise_for_status()
                blob = resp.content
                dest.write_bytes(blob)
                log(f"[SEC] {label} done ({len(blob)/1024**2:.0f} MB)")

            with zipfile.ZipFile(io.BytesIO(blob)) as zf:
                names = [i.filename for i in zf.infolist()]
                say(f"**{label}** - zip 내부 파일: {', '.join(f'`{n}`' for n in names)}")
                say()

                info = load_13f_table(zf, "INFOTABLE")
                sub = load_13f_table(zf, "SUBMISSION")
                cov = load_13f_table(zf, "COVERPAGE")

                if info is not None:
                    infotables[label] = info
                    if label == first_label:
                        profile(info, f"sec_{label}_INFOTABLE",
                                "보유 종목 명세. 이 프로젝트의 본체 테이블입니다.")
                if sub is not None and label == first_label:
                    profile(sub, f"sec_{label}_SUBMISSION",
                            "`FILING_DATE` 와 `PERIODOFREPORT` 가 여기 있습니다. "
                            "45일 지연을 다루려면 이 두 컬럼이 핵심입니다.")
                if cov is not None and label == first_label:
                    profile(cov, f"sec_{label}_COVERPAGE",
                            "`FILINGMANAGER_NAME` - 운용사 이름.")

        except Exception as e:
            say(f"**{label} 실패** - `{e!r}`")
            say()

    # -- 45일 공시 지연을 실제 숫자로 확인
    if infotables and first_label:
        latest = first_label
        say("### 검증 1 - 45일 공시 지연이 실제로 있는가")
        say()
        try:
            dest = RAW / f"{latest}_form13f.zip"
            with zipfile.ZipFile(dest) as zf:
                sub = load_13f_table(zf, "SUBMISSION")
            sub["FILING_DATE"] = pd.to_datetime(sub["FILING_DATE"], errors="coerce", format="mixed")
            sub["PERIODOFREPORT"] = pd.to_datetime(sub["PERIODOFREPORT"], errors="coerce", format="mixed")
            lag = (sub["FILING_DATE"] - sub["PERIODOFREPORT"]).dt.days.dropna()
            say(f"{latest} 제출 {len(lag):,}건의 `FILING_DATE - PERIODOFREPORT` (일):")
            say()
            say("| 통계 | 일수 |")
            say("|---|---:|")
            for k, v in [("최소", lag.min()), ("25%", lag.quantile(.25)), ("중앙값", lag.median()),
                         ("75%", lag.quantile(.75)), ("최대", lag.max())]:
                say(f"| {k} | {v:,.0f} |")
            say()
            say(f"45일 넘겨 제출된 건: **{(lag > 45).mean()*100:.1f}%**")
            say()
            say("> 중앙값이 40일대라면 45일 규칙이 데이터에서 확인된 것입니다. "
                "`PERIODOFREPORT` 를 분석 시점으로 쓰면 이만큼의 미래 정보를 쓰게 됩니다.")
            say()
        except Exception as e:
            say(f"확인 실패 - `{e!r}`")
            say()

    # -- 단위 전환 흔적 확인
    if len(infotables) >= 1:
        say("### 검증 2 - VALUE 단위 (천달러 vs 달러)")
        say()
        say("`VALUE / SSHPRNAMT` 는 주당 단가입니다. 단위가 천달러면 이 값이 비정상적으로 작게 나옵니다.")
        say()
        say("| 분기 | 중앙 단가 | 판정 |")
        say("|---|---:|---|")
        for label, info in infotables.items():
            try:
                v = pd.to_numeric(info["VALUE"], errors="coerce")
                s = pd.to_numeric(info["SSHPRNAMT"], errors="coerce")
                px = (v / s).replace([float("inf"), float("-inf")], pd.NA).dropna()
                px = px[(px > 0) & (px < 1e7)]
                med = px.median()
                verdict = "달러 단위로 보입니다" if med > 1 else "**천달러 단위로 보입니다**"
                say(f"| {label} | {med:,.4f} | {verdict} |")
            except Exception as e:
                say(f"| {label} | - | 실패 `{e!r}` |")
        say()
        say("> 2023년 1월 3일 전후 분기를 같이 받으면 이 표에서 1000배 차이가 눈에 보입니다. "
            "이게 2차 산출물의 '데이터 품질 확인' 절 첫 번째 항목이 됩니다.")
        say()


# -------------------------------------------------------------- 후보 B: KRX


def probe_krx() -> None:
    say("## 후보 B - KRX 투자자별 거래실적")
    say()

    try:
        from pykrx import stock
    except Exception as e:
        say(f"**실패** - pykrx 를 못 불러왔습니다: `{e!r}`")
        say()
        return

    end = date.today() - timedelta(days=3)      # T+2 지연 감안
    start = end - timedelta(days=365 * 3)
    s, e = start.strftime("%Y%m%d"), end.strftime("%Y%m%d")
    say(f"요청 구간: `{s}` ~ `{e}` (T+2 지연을 감안해 3일 전까지)")
    say()

    # 1) 시장 전체 투자자별 순매수
    try:
        log("[KRX] market trading value by investor ...")
        df = stock.get_market_trading_value_by_investor(s, e, "KOSPI")
        df = df.reset_index()
        profile(df, "krx_kospi_by_investor",
                "KOSPI 전체, 투자자 유형별 매수/매도/순매수 금액. 구간 합계로 나옵니다.")
    except Exception as ex:
        say(f"**시장 전체 조회 실패** - `{ex!r}`")
        say("> 스크래퍼가 깨졌을 가능성이 있습니다. 후보 B의 재현성 리스크가 바로 이것입니다.")
        say()

    # 2) 일별 시계열 (삼성전자)
    try:
        log("[KRX] daily series for 005930 ...")
        s1 = (end - timedelta(days=365)).strftime("%Y%m%d")   # 일별은 1년만 (스크래핑 부담)
        d2 = stock.get_market_trading_value_by_date(s1, e, "005930")
        d2 = d2.reset_index()
        profile(d2, "krx_005930_daily_by_investor",
                "삼성전자(005930) 일별 투자자별 순매수. 시계열 분석의 최소 단위입니다.")
    except Exception as ex:
        say(f"**일별 시계열 조회 실패** - `{ex!r}`")
        say()

    # 3) 주가 (대조용)
    try:
        log("[KRX] OHLCV for 005930 ...")
        d3 = stock.get_market_ohlcv(s, e, "005930").reset_index()
        profile(d3, "krx_005930_ohlcv", "삼성전자 일별 시세. 순매수와 붙여 성과를 봅니다.")
    except Exception as ex:
        say(f"**시세 조회 실패** - `{ex!r}`")
        say()


# -------------------------------------------------------------- main


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", choices=["sec", "krx"], help="한 후보만 확인")
    ap.add_argument("--list", action="store_true",
                    help="다운로드 없이 받을 수 있는 13F 분기 목록만 확인 (몇 초)")
    ap.add_argument("--quarters", type=int, default=2, help="최근 몇 분기를 받을지 (기본 2)")
    ap.add_argument("--also", default="2022q3",
                    help="단위 전환 비교용으로 추가로 받을 분기. 예: 2022q3. 끄려면 --also \"\"")
    args = ap.parse_args()

    OUT.mkdir(parents=True, exist_ok=True)

    say("# 후보 데이터 실물 확인 리포트")
    say()
    say(f"실행 {date.today():%Y-%m-%d} - pandas {pd.__version__} - python {sys.version.split()[0]}")
    say()
    say("이 리포트는 문서상 스펙과 실제 데이터가 일치하는지 대조하기 위한 것입니다.")
    say()
    say("---")
    say()

    if args.only in (None, "sec"):
        also = [x.strip() for x in args.also.split(",") if x.strip()]
        probe_sec(args.quarters, also, list_only=args.list)
        say("---")
        say()
    if args.only in (None, "krx") and not args.list:
        probe_krx()

    report = OUT / "report.md"
    report.write_text("\n".join(LINES) + "\n", encoding="utf-8")

    log("")
    log(f"[done] report -> {report}")
    log(f"[done] samples -> {SAMPLES}")
    log("")
    log("Send probe_out/report.md and probe_out/samples/ to Claude.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
