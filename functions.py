import os
import pandas as pd

USERS_FILE = "users.csv"
RECORDS_FILE = "tax_records.csv"

USER_COLUMNS = ["user_id", "ic_number"]
RECORD_COLUMNS = [
    "user_id", "test_case_id", "year_of_assessment", "annual_income",
    "total_tax_relief", "chargeable_income", "tax_before_rebate",
    "tax_rebate", "final_tax_payable",
]
TAX_BRACKETS = [
    (5000.0,      0.00),
    (20000.0,     0.01),
    (35000.0,     0.03),
    (50000.0,     0.06),
    (70000.0,     0.11),
    (100000.0,    0.19),
    (400000.0,    0.25),
    (600000.0,    0.26),
    (2000000.0,   0.28),
    (float("inf"), 0.30),
]

INDIVIDUAL_RELIEF  = 9000.0
REBATE_AMOUNT      = 400.0
REBATE_THRESHOLD   = 35000.0
YEAR_OF_ASSESSMENT = 2026

def ensure_files():
    """Create empty CSV files with headers if they do not exist."""
    if not os.path.exists(USERS_FILE):
        df_users = pd.DataFrame(columns=USER_COLUMNS)
        df_users.to_csv(USERS_FILE, index=False)
        
    if not os.path.exists(RECORDS_FILE):
        df_records = pd.DataFrame(columns=RECORD_COLUMNS)
        df_records.to_csv(RECORDS_FILE, index=False)


def load_users():
    """Return registered users as a LIST OF DICTIONARIES."""
    if not os.path.exists(USERS_FILE):
        return []
    try:
        df = pd.read_csv(USERS_FILE, dtype=str)
    except (pd.errors.EmptyDataError, pd.errors.ParserError, OSError):
        return []
    df = df.fillna("")
    for col in USER_COLUMNS:
        if col not in df.columns:
            df[col] = ""
    return df[USER_COLUMNS].to_dict("records")


def save_users(users):
    """users = list of dicts -> DataFrame -> users.csv"""
    try:
        df = pd.DataFrame(users, columns=USER_COLUMNS)
        df.to_csv(USERS_FILE, index=False)
        return True
    except OSError as e:
        print(f"[Error] Could not save users: {e}")
        return False

def validate_user_id(user_id):
    user_id = user_id.strip()
    if not 4 <= len(user_id) <= 20:
        return False, "User ID must be 4-20 characters."
    if not user_id.isalnum():
        return False, "User ID may contain letters and digits only."
    return True, "OK"

def validate_ic(ic):
    ic = ic.strip()
    if len(ic) != 12 or not ic.isdigit():
        return False, "IC number must be exactly 12 digits."
    return True, "OK"

def register_user(user_id, ic):
    """Validate, reject duplicates, append to list, save CSV."""
    ok, msg = validate_user_id(user_id)
    if not ok:
        return False, msg
    ok, msg = validate_ic(ic)
    if not ok:
        return False, msg

    users = load_users()
    uid_check = user_id.strip().lower()
    if any(u["user_id"].lower() == uid_check for u in users):
        return False, "That User ID is already registered."
        
    if any(u["ic_number"] == ic.strip() for u in users):
        return False, "That IC number is already registered."

    users.append({"user_id": user_id.strip(), "ic_number": ic.strip()})
    if not save_users(users):
        return False, "Registration failed while writing users.csv."
        
    pwd = ic.strip()[-4:]
    msg = f"Registration successful. Password = last 4 IC digits ({pwd})."
    return True, msg


def authenticate_user(user_id, password):
    """Password = last four digits of the registered IC."""
    for u in load_users():
        if u["user_id"].lower() == user_id.strip().lower():
            return u["ic_number"][-4:] == password.strip()
    return False

def calculate_chargeable_income(annual_income, total_relief):
    """Chargeable income, never negative."""
    return max(annual_income - total_relief, 0.0)

def calculate_tax_before_rebate(chargeable_income):
    """Apply progressive rates band by band."""
    tax, lower = 0.0, 0.0
    for upper, rate in TAX_BRACKETS:
        if chargeable_income <= lower:
            break
        taxable_in_band = min(chargeable_income, upper) - lower
        tax += taxable_in_band * rate
        lower = upper
    return round(tax, 2)

def calculate_rebate(chargeable_income):
    """RM400 individual rebate only if chargeable income <= RM35,000."""
    return REBATE_AMOUNT if chargeable_income <= REBATE_THRESHOLD else 0.0

def calculate_tax(annual_income, total_relief):
    """Return a dictionary with every figure the report needs."""
    chargeable = calculate_chargeable_income(annual_income, total_relief)
    before     = calculate_tax_before_rebate(chargeable)
    rebate     = calculate_rebate(chargeable)
    final      = max(before - rebate, 0.0)
    return {
        "year_of_assessment": YEAR_OF_ASSESSMENT,
        "annual_income":      round(annual_income, 2),
        "total_tax_relief":   round(total_relief, 2),
        "chargeable_income":  round(chargeable, 2),
        "tax_before_rebate":  round(before, 2),
        "tax_rebate":         round(rebate, 2),
        "final_tax_payable":  round(final, 2),
    }

def build_tax_record(user_id, result, test_case_id=None):
    """Merge the calculation dict with the owner identifiers."""
    record = {"user_id": user_id, "test_case_id": test_case_id}
    record.update(result)
    return record

def save_records(records):
    """records = LIST of dicts -> DataFrame -> append to tax_records.csv."""
    if not records:
        return False
    try:
        existing = load_tax_records()
        new_df   = pd.DataFrame(records, columns=RECORD_COLUMNS)
        combined = pd.concat([existing, new_df], ignore_index=True)
        combined.to_csv(RECORDS_FILE, index=False)
        return True
    except OSError as e:
        print(f"[Error] Could not save records: {e}")
        return False


def load_tax_records(user_id=None):
    """Read tax_records.csv, optionally filtered to one user."""
    if not os.path.exists(RECORDS_FILE):
        return pd.DataFrame(columns=RECORD_COLUMNS)
    try:
        df = pd.read_csv(RECORDS_FILE)
    except (pd.errors.EmptyDataError, pd.errors.ParserError, OSError):
        return pd.DataFrame(columns=RECORD_COLUMNS)
    for col in RECORD_COLUMNS:
        if col not in df.columns:
            df[col] = None
    if user_id is not None:
        uid_check = user_id.strip().lower()
        df = df[df["user_id"].astype(str).str.lower() == uid_check]
    return df.reset_index(drop=True)

def format_rm(value):
    return f"RM {value:,.2f}"

def display_records(df):
    if df is None or df.empty:
        print("No records found.")
        return
    show = df.copy()
    money_cols = [
        "annual_income", "total_tax_relief", "chargeable_income",
        "tax_before_rebate", "tax_rebate", "final_tax_payable"
    ]
    for col in money_cols:
        show[col] = pd.to_numeric(show[col], errors="coerce").map(
            lambda v: f"{v:,.2f}" if pd.notna(v) else "")
    show["test_case_id"] = show["test_case_id"].fillna("")
    print(show.to_string(index=False))

def prompt_amount(prompt):
    """Loop until a valid non-negative number is entered; '' cancels."""
    while True:
        raw = input(prompt).strip().replace(",", "").replace("RM", "").strip()
        if raw == "":
            return None
        try:
            value = float(raw)
        except ValueError:
            print("  Invalid input: please enter a number (e.g. 40000).")
            continue
        if value < 0:
            print("  Amount cannot be negative.")
            continue
        if value > 100_000_000:
            print("  That figure looks unrealistic. Please re-enter.")
            continue
        return value


TEST_CASES = [
    {"test_case_id": "T01", "annual_income":  9000.0, 
     "total_tax_relief":  9000.0},
    {"test_case_id": "T02", "annual_income": 40000.0, 
     "total_tax_relief":  9000.0},
    {"test_case_id": "T03", "annual_income": 65000.0, 
     "total_tax_relief": 14000.0},
    {"test_case_id": "T04", "annual_income": 120000.0, 
     "total_tax_relief": 18000.0},
    {"test_case_id": "T05", "annual_income": 83000.0, 
     "total_tax_relief": 12000.0},
]

def run_test_cases():
    """Compute T01-T05, replace old copies, save to tax_records.csv."""
    records = []
    for tc in TEST_CASES:
        result = calculate_tax(tc["annual_income"], tc["total_tax_relief"])
        record = build_tax_record("SYSTEM", result, tc["test_case_id"])
        records.append(record)

    existing = load_tax_records()
    if not existing.empty:
        tc_ids = [tc["test_case_id"] for tc in TEST_CASES]
        keep = ~existing["test_case_id"].astype(str).isin(tc_ids)
        existing = existing[keep]
        
    new_df = pd.DataFrame(records, columns=RECORD_COLUMNS)
    combined = pd.concat([existing, new_df], ignore_index=True)
    
    try:
        combined.to_csv(RECORDS_FILE, index=False)
        return True, records
    except OSError as e:
        return False, str(e)