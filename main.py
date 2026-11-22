import functions as fn

def registration_screen():
    print("\n--- New User Registration ---")
    user_id  = input("Choose a User ID (4-20 letters/digits): ")
    ic       = input("Enter your 12-digit IC number: ")
    ok, msg  = fn.register_user(user_id, ic)
    status = "[OK] " if ok else "[Failed] "
    print(status + msg)

def login_screen():
    print("\n--- Login ---")
    user_id  = input("User ID : ")
    password = input("Password (last 4 digits of IC): ")
    if fn.authenticate_user(user_id, password):
        print(f"[OK] Welcome back, {user_id.strip()}!")
        return user_id.strip()
    print("[Failed] Invalid User ID or password.")
    return None

def calculate_screen(user_id, record_list):
    print("\n--- Tax Calculation ---")
    income = fn.prompt_amount("Annual income (RM): ")
    if income is None:
        print("Cancelled.")
        return
    relief = fn.prompt_amount("Total eligible tax relief (RM): ")
    if relief is None:
        print("Cancelled.")
        return

    result = fn.calculate_tax(income, relief)

    print("\n===== TAX CALCULATION RESULT =====")
    print(f"Year of Assessment      : {result['year_of_assessment']}")
    print(f"Annual Income           : {fn.format_rm(result['annual_income'])}")
    
    relief_val = result['total_tax_relief']
    print(f"Total Tax Relief        : {fn.format_rm(relief_val)}")
    
    charge_val = result['chargeable_income']
    print(f"Chargeable Income       : {fn.format_rm(charge_val)}")
    
    before_val = result['tax_before_rebate']
    print(f"Tax Before Rebate       : {fn.format_rm(before_val)}")
    
    rebate_val = result['tax_rebate']
    print(f"Tax Rebate              : {fn.format_rm(rebate_val)}")
    
    final_val = result['final_tax_payable']
    print(f"Final Tax Payable       : {fn.format_rm(final_val)}")
    print("==================================")

    record = fn.build_tax_record(user_id, result)
    record_list.append(record)

    save_prompt = "\nSave this record to tax_records.csv? (y/n): "
    if input(save_prompt).strip().lower() == "y":
        if fn.save_records(record_list):
            print("[OK] Record saved.")
            record_list.clear()
        else:
            print("[Failed] Record could not be saved.")

def user_menu(user_id):
    record_list = []
    while True:
        print(f"\n===== LOGGED IN AS {user_id} =====")
        print("1. Calculate income tax")
        print("2. View my saved records")
        print("3. View all records (pandas DataFrame)")
        print("4. Log out")
        choice = input("Select (1-4): ").strip()

        if choice == "1":
            calculate_screen(user_id, record_list)
        elif choice == "2":
            user_df = fn.load_tax_records(user_id)
            fn.display_records(user_df)
        elif choice == "3":
            df = fn.load_tax_records()
            print("\n--- DataFrame from tax_records.csv ---")
            print(df.to_string(index=False))
        elif choice == "4":
            print("Logged out.")
            return
        else:
            print("Invalid choice.")

def main():
    fn.ensure_files()
    while True:
        print("\n===== MALAYSIAN TAX INPUT PROGRAM (YA 2026) =====")
        print("1. Register")
        print("2. Login")
        print("3. Run & save test cases T01-T05")
        print("4. Exit")
        choice = input("Select (1-4): ").strip()

        if choice == "1":
            registration_screen()
        elif choice == "2":
            user_id = login_screen()
            if user_id:
                user_menu(user_id)
        elif choice == "3":
            ok, data = fn.run_test_cases()
            if ok:
                print("[OK] Test cases saved.")
                for r in data:
                    print(
                        f"  {r['test_case_id']}: chargeable "
                        f"{r['chargeable_income']:,.2f} | tax "
                        f"{r['tax_before_rebate']:,.2f} | rebate "
                        f"{r['tax_rebate']:,.2f} | final "
                        f"{r['final_tax_payable']:,.2f}"
                    )
            else:
                print(f"[Failed] {data}")
        elif choice == "4":
            print("Goodbye.")
            break
        else:
            print("Invalid choice, please enter 1-4.")


if __name__ == "__main__":
    main()