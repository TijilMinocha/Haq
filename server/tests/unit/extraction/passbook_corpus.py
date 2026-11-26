"""Synthetic passbook pages, one per layout and OCR failure the parser has to survive.

Every name, account number and amount here is invented. The pages are plain text because
`OcrPage.from_text` turns them into the same word-and-column structure OCR hands the parser.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class ExpectedTxn:
    date: str
    """ISO date."""
    narration: str
    amount: int
    direction: str | None
    """None when nothing on the row says whether it is a debit or a credit."""


@dataclass(frozen=True)
class Sample:
    name: str
    text: str
    transactions: tuple[ExpectedTxn, ...]
    account_holder: str | None = None
    bank: str | None = None
    branch: str | None = None
    ifsc: str | None = None
    account_last4: str | None = None
    nominee_name: str | None = None


def txn(date: str, narration: str, amount: int, direction: str | None = "debit") -> ExpectedTxn:
    return ExpectedTxn(date, narration, amount, direction)


_DEVANAGARI_DIGITS = str.maketrans("0123456789", "".join(chr(0x0966 + i) for i in range(10)))


def devanagari(text: str) -> str:
    """Renders the digits of an already-written page the way a Hindi passbook prints them."""
    return text.translate(_DEVANAGARI_DIGITS)


SAMPLES: tuple[Sample, ...] = (
    Sample(
        name="sbi_standard_columns",
        text="""
STATE BANK OF INDIA
Branch: SEELAMPUR IFSC: SBIN0000001
Name: KAMLA DEVI
A/c No: 00000012345678901
Nominee: PHOOLMATI DEVI
Date        Particulars                Chq         Withdrawal    Deposit      Balance
01-05-2026  BALANCE B/F                                        5,000.00
28-05-2026  PMJJBY PREMIUM                          436.00                 4,564.00
30-05-2026  PMSBY PREMIUM                            20.00                 4,544.00
02-10-2026  BY CASH                                              3,000.00  7,544.00
30-10-2026  ATM WDL SEELAMPUR                     2,000.00                 5,544.00
""",
        transactions=(
            txn("2026-05-28", "PMJJBY PREMIUM", 436),
            txn("2026-05-30", "PMSBY PREMIUM", 20),
            txn("2026-10-02", "BY CASH", 3000, "credit"),
            txn("2026-10-30", "ATM WDL SEELAMPUR", 2000),
        ),
        account_holder="Kamla Devi",
        bank="SBI",
        branch="SEELAMPUR",
        ifsc="SBIN0000001",
        account_last4="8901",
        nominee_name="Phoolmati Devi",
    ),
    Sample(
        name="sbi_value_date_column",
        text="""
STATE BANK OF INDIA
Branch: DILSHAD GARDEN IFSC: SBIN0000002
Name: ARJUN SINGH
A/c No: 00000022223333444
Nominee: NOT REGISTERED
Date        Value Date  Particulars              Withdrawal   Deposit    Balance
01-05-2026  01-05-2026  BALANCE B/F                               4,000.00
28-05-2026  29-05-2026  PMJJBY/RENEWAL/2026          436.00                3,564.00
12-06-2026  12-06-2026  TO PMJJBY INS                 20.00                3,544.00
05-07-2026  06-07-2026  BY SALARY CR                            12,000.00 15,544.00
""",
        transactions=(
            txn("2026-05-28", "PMJJBY/RENEWAL/2026", 436),
            txn("2026-06-12", "TO PMJJBY INS", 20),
            txn("2026-07-05", "BY SALARY CR", 12000, "credit"),
        ),
        account_holder="Arjun Singh",
        bank="SBI",
        branch="DILSHAD GARDEN",
        ifsc="SBIN0000002",
        account_last4="3444",
    ),
    Sample(
        name="pnb_cr_marker_glued_to_amount",
        text="""
PUNJAB NATIONAL BANK
Branch: LAXMI NAGAR IFSC: PUNB0111100
Name: SURESH YADAV
Account Number: 00000055556666777
Nominee: MEENA DEVI
Date Particulars Withdrawal Deposit Balance
01-05-2026 BALANCE B/F 6,000.00
28-05-2026 PMSBY PREM 20.00 5,980.00
28-05-2026 PMJJBY PREMIUM 436.00 5,544.00
11-08-2026 BY TRANSFER 4,564.00Cr 10,108.00
""",
        transactions=(
            txn("2026-05-28", "PMSBY PREM", 20),
            txn("2026-05-28", "PMJJBY PREMIUM", 436),
            txn("2026-08-11", "BY TRANSFER", 4564, "credit"),
        ),
        account_holder="Suresh Yadav",
        bank="PNB",
        branch="LAXMI NAGAR",
        ifsc="PUNB0111100",
        account_last4="6777",
        nominee_name="Meena Devi",
    ),
    Sample(
        name="bob_dr_cr_marker_as_a_word",
        text="""
BANK OF BARODA
Branch: KAROL BAGH IFSC: BARB0TEST01
Name: RAJU PRASAD
A/c No: 00000077778888999
Nominee: SUNITA DEVI
Date Particulars Withdrawal Deposit Balance
01-05-2026 BALANCE B/F 2,000.00
28-05-2026 TO PMJJBY INS 436.00 Dr 1,564.00
30-05-2026 PMSBY PREM 20.00 Dr 1,544.00
03-06-2026 BY CASH DEPOSIT 3,000.00 CR 4,544.00
""",
        transactions=(
            txn("2026-05-28", "TO PMJJBY INS", 436),
            txn("2026-05-30", "PMSBY PREM", 20),
            txn("2026-06-03", "BY CASH DEPOSIT", 3000, "credit"),
        ),
        account_holder="Raju Prasad",
        bank="Bank of Baroda",
        branch="KAROL BAGH",
        ifsc="BARB0TEST01",
        account_last4="8999",
        nominee_name="Sunita Devi",
    ),
    Sample(
        name="canara_month_name_dates",
        text="""
CANARA BANK
Branch: MAYUR VIHAR IFSC: CNRB0000123
Name: MEENA KUMARI
A/c No: 00000099990000111
Nominee: KAMLA BAI
Date Particulars Withdrawal Deposit Balance
01 May 2026 BALANCE B/F 8,000.00
28 May 2026 JEEVAN JYOTI BIMA 436.00 7,564.00
28-MAY-26 SURAKSHA BIMA YOJANA 20.00 7,544.00
""",
        transactions=(
            txn("2026-05-28", "JEEVAN JYOTI BIMA", 436),
            txn("2026-05-28", "SURAKSHA BIMA YOJANA", 20),
        ),
        account_holder="Meena Kumari",
        bank="Canara Bank",
        branch="MAYUR VIHAR",
        ifsc="CNRB0000123",
        account_last4="0111",
        nominee_name="Kamla Bai",
    ),
    Sample(
        name="union_bank_amounts_without_paise",
        text="""
UNION BANK OF INDIA
Branch: PREET VIHAR IFSC: UBIN0550001
Name: RAJESH GUPTA
A/c No: 00000033338888999
Nominee: ASHA DEVI
Date Particulars Withdrawal Deposit Balance
01-05-2026 BALANCE B/F 3,000
28-05-2026 PMJJBY PREM 436 2,564
30-05-2026 PMSBY PREM 20 2,544
""",
        transactions=(
            txn("2026-05-28", "PMJJBY PREM", 436),
            txn("2026-05-30", "PMSBY PREM", 20),
        ),
        account_holder="Rajesh Gupta",
        bank="Union Bank of India",
        branch="PREET VIHAR",
        ifsc="UBIN0550001",
        account_last4="8999",
        nominee_name="Asha Devi",
    ),
    Sample(
        name="bank_of_india_single_amount_column",
        text="""
BANK OF INDIA
Branch: GANDHI NAGAR IFSC: BKID0006012
Name: DINESH KUMAR
A/c No: 00000044445555666
Nominee: REKHA DEVI
Date Particulars Amount
28-05-2026 PMJJBY PREMIUM 436.00
30-05-2026 PMSBY PREMIUM 20.00
12-06-2026 BY CLG NEFT CR 1,500.00
14-06-2026 TO ATM WDL 500.00
24-06-2026 REVERSAL OF ATM WDL CHARGES 25.00
""",
        transactions=(
            txn("2026-05-28", "PMJJBY PREMIUM", 436),
            txn("2026-05-30", "PMSBY PREMIUM", 20),
            txn("2026-06-12", "BY CLG NEFT CR", 1500, "credit"),
            txn("2026-06-14", "TO ATM WDL", 500),
            txn("2026-06-24", "REVERSAL OF ATM WDL CHARGES", 25, "credit"),
        ),
        account_holder="Dinesh Kumar",
        bank="Bank of India",
        branch="GANDHI NAGAR",
        ifsc="BKID0006012",
        account_last4="5666",
        nominee_name="Rekha Devi",
    ),
    Sample(
        name="india_post_hindi_labels_and_digits",
        text=(
            """
भारत डाक विभाग
शाखा: सीलमपुर IFSC: IPOS0000001
नाम / Name : राजू प्रसाद
खाता संख्या : 00000012345678902
नामांकित : कमला देवी
दिनांक विवरण जमा निकासी शेष
"""
            + devanagari(
                """
01-05-2026 शेष आगे 5,000.00
28-05-2026 पीएमजेजेबीवाई प्रीमियम 436.00 4,564.00
30-05-2026 पीएमएसबीवाई प्रीमियम 20.00 4,544.00
"""
            )
        ),
        transactions=(
            txn("2026-05-28", "पीएमजेजेबीवाई प्रीमियम", 436),
            txn("2026-05-30", "पीएमएसबीवाई प्रीमियम", 20),
        ),
        account_holder="राजू प्रसाद",
        bank="India Post",
        branch="सीलमपुर",
        ifsc="IPOS0000001",
        account_last4="8902",
        nominee_name="कमला देवी",
    ),
    Sample(
        name="union_bank_sby_renewal_and_transfer",
        text="""
UNION BANK OF INDIA
Branch: MAYUR VIHAR III IFSC: UBIN0550002
Name: SANJAY VERMA
A/c No: 00000066667777888
Nominee: KIRAN DEVI
Date Particulars Withdrawal Deposit Balance
01-05-2026 BALANCE B/F 1,00,000.00
07-06-2026 SBY RENEWAL 20.00 99,980.00
07-06-2026 TRF TO PMSBY 20.00 99,960.00
08-06-2026 SBY RENEWAL REVERSAL 20.00 99,980.00
""",
        transactions=(
            txn("2026-06-07", "SBY RENEWAL", 20),
            txn("2026-06-07", "TRF TO PMSBY", 20),
            txn("2026-06-08", "SBY RENEWAL REVERSAL", 20, "credit"),
        ),
        account_holder="Sanjay Verma",
        bank="Union Bank of India",
        branch="MAYUR VIHAR III",
        ifsc="UBIN0550002",
        account_last4="7888",
        nominee_name="Kiran Devi",
    ),
    Sample(
        name="bob_atal_pension_is_not_a_premium",
        text="""
BANK OF BARODA
Branch: JANAKPURI IFSC: BARB0TEST02
Name: ATAL BIHARI SHARMA
A/c No: 00000088889999000
Nominee: NONE
Date Particulars Withdrawal Deposit Balance
01-05-2026 BALANCE B/F 5,000.00
05-06-2026 ATAL PENSION YOJANA CONTRIBUTION 1,000.00 4,000.00
07-06-2026 PMJJBY PREM 436.00 3,564.00
""",
        transactions=(
            txn("2026-06-05", "ATAL PENSION YOJANA CONTRIBUTION", 1000),
            txn("2026-06-07", "PMJJBY PREM", 436),
        ),
        account_holder="Atal Bihari Sharma",
        bank="Bank of Baroda",
        branch="JANAKPURI",
        ifsc="BARB0TEST02",
        account_last4="9000",
    ),
    Sample(
        name="sbi_premium_reversal_is_a_credit",
        text="""
STATE BANK OF INDIA
Branch: SEEMAPURI IFSC: SBIN0000003
Name: PHOOLMATI DEVI
A/c No: 00000011112222333
Nominee: KAMLA DEVI
Date Particulars Withdrawal Deposit Balance
01-05-2026 BALANCE B/F 4,500.00
28-05-2026 PMJJBY PREMIUM 436.00 4,064.00
30-09-2026 PMJJBY PREM REVERSAL 436.00 4,500.00
""",
        transactions=(
            txn("2026-05-28", "PMJJBY PREMIUM", 436),
            txn("2026-09-30", "PMJJBY PREM REVERSAL", 436, "credit"),
        ),
        account_holder="Phoolmati Devi",
        bank="SBI",
        branch="SEEMAPURI",
        ifsc="SBIN0000003",
        account_last4="2333",
        nominee_name="Kamla Devi",
    ),
    Sample(
        name="pnb_atm_withdrawals",
        text="""
PUNJAB NATIONAL BANK
Branch: KRISHNA NAGAR IFSC: PUNB0111101
Name: MOHAN LAL
A/c No: 00000022223333445
Nominee: SHANTI DEVI
Date Particulars Withdrawal Deposit Balance
01-05-2026 BALANCE B/F 9,000.00
28-05-2026 ATM WDL KRISHNA NAGAR 2,000.00 7,000.00
29-05-2026 ATM WDL CASH 3,000.00 4,000.00
""",
        transactions=(
            txn("2026-05-28", "ATM WDL KRISHNA NAGAR", 2000),
            txn("2026-05-29", "ATM WDL CASH", 3000),
        ),
        account_holder="Mohan Lal",
        bank="PNB",
        branch="KRISHNA NAGAR",
        ifsc="PUNB0111101",
        account_last4="3445",
        nominee_name="Shanti Devi",
    ),
    Sample(
        name="canara_atw_nfs_reference",
        text="""
CANARA BANK
Branch: ROHINI IFSC: CNRB0000124
Name: VINOD KUMAR
A/c No: 00000033334444555
Nominee: ASHA KUMARI
Date Particulars Withdrawal Deposit Balance
01/05/26 BALANCE B/F 6,500.00
28/05/26 ATW/NFS/5432109876/ROHINI 1,500.00 5,000.00
29/05/26 ATW/NFS/5432109877/ROHINI 500.00 4,500.00
""",
        transactions=(
            txn("2026-05-28", "ATW/NFS/5432109876/ROHINI", 1500),
            txn("2026-05-29", "ATW/NFS/5432109877/ROHINI", 500),
        ),
        account_holder="Vinod Kumar",
        bank="Canara Bank",
        branch="ROHINI",
        ifsc="CNRB0000124",
        account_last4="4555",
        nominee_name="Asha Kumari",
    ),
    Sample(
        name="sbi_pos_purchase_with_wrapped_narration",
        text="""
STATE BANK OF INDIA
Branch: LAXMI NAGAR IFSC: SBIN0000004
Name: POOJA RANI
A/c No: 00000044445555667
Nominee: RAJESH KUMAR
Date Particulars Withdrawal Deposit Balance
01-05-2026 BALANCE B/F 3,000.00
28-05-2026 POS/PRCH/7788990011 650.00 2,350.00
KIRANA STORE LAXMI NAGAR
29-05-2026 POS/PRCH/7788990022 100.00 2,250.00
""",
        transactions=(
            txn("2026-05-28", "POS/PRCH/7788990011 KIRANA STORE LAXMI NAGAR", 650),
            txn("2026-05-29", "POS/PRCH/7788990022", 100),
        ),
        account_holder="Pooja Rani",
        bank="SBI",
        branch="LAXMI NAGAR",
        ifsc="SBIN0000004",
        account_last4="5667",
        nominee_name="Rajesh Kumar",
    ),
    Sample(
        name="bank_of_india_matm",
        text="""
BANK OF INDIA
Branch: BHAJANPURA IFSC: BKID0006013
Name: SUNIL KUMAR
A/c No: 00000055556666778
Nominee: MEENA DEVI
Date Particulars Withdrawal Deposit Balance
01-05-2026 BALANCE B/F 2,500.00
28-05-2026 MATM/BC/4521 1,000.00 1,500.00
""",
        transactions=(txn("2026-05-28", "MATM/BC/4521", 1000),),
        account_holder="Sunil Kumar",
        bank="Bank of India",
        branch="BHAJANPURA",
        ifsc="BKID0006013",
        account_last4="6778",
        nominee_name="Meena Devi",
    ),
    Sample(
        name="india_post_csp_withdrawal",
        text="""
INDIA POST
Branch: SADAR BAZAR IFSC: IPOS0000002
Name: GUDDI DEVI
A/c No: 00000066667777889
Nominee: RAMESH PRASAD
Date Particulars Withdrawal Deposit Balance
01-05-2026 BALANCE B/F 1,200.00
28-05-2026 CSP WDL SADAR BAZAR 500.00 700.00
""",
        transactions=(txn("2026-05-28", "CSP WDL SADAR BAZAR", 500),),
        account_holder="Guddi Devi",
        bank="India Post",
        branch="SADAR BAZAR",
        ifsc="IPOS0000002",
        account_last4="7889",
        nominee_name="Ramesh Prasad",
    ),
    Sample(
        name="union_bank_upi_and_aeps",
        text="""
UNION BANK OF INDIA
Branch: DWARKA IFSC: UBIN0550003
Name: ANITA SHARMA
A/c No: 00000077778888990
Nominee: SURAJ SHARMA
Date Particulars Withdrawal Deposit Balance
01-05-2026 BALANCE B/F 5,000.00
28-05-2026 UPI/P2M/998877665544/KIRANA 250.00 4,750.00
28-05-2026 UPI/P2A/112233445566/ANITA 1,000.00 5,750.00
29-05-2026 AEPS/CASH WDL/445566 500.00 5,250.00
""",
        transactions=(
            txn("2026-05-28", "UPI/P2M/998877665544/KIRANA", 250),
            txn("2026-05-28", "UPI/P2A/112233445566/ANITA", 1000, "credit"),
            txn("2026-05-29", "AEPS/CASH WDL/445566", 500),
        ),
        account_holder="Anita Sharma",
        bank="Union Bank of India",
        branch="DWARKA",
        ifsc="UBIN0550003",
        account_last4="8990",
        nominee_name="Suraj Sharma",
    ),
    Sample(
        name="pnb_letter_for_digit_swaps",
        text="""
PUNJAB NATIONAL BANK
Branch: KAMLA NAGAR IFSC: PUNB0111102
Name: BABLU YADAV
A/c No: 00000088889999001
Nominee: SONI DEVI
Date Particulars Withdrawal Deposit Balance
OI-O5-2O26 BALANCE B/F 5,000.00
2B-O5-2O26 PMJJBY PREMIUM S36.OO 4,464.00
3O-O5-2O26 PMSBY PREM 2O.OO 4,444.00
""",
        transactions=(
            txn("2026-05-28", "PMJJBY PREMIUM", 536),
            txn("2026-05-30", "PMSBY PREM", 20),
        ),
        account_holder="Bablu Yadav",
        bank="PNB",
        branch="KAMLA NAGAR",
        ifsc="PUNB0111102",
        account_last4="9001",
        nominee_name="Soni Devi",
    ),
    Sample(
        name="canara_missing_decimal_point",
        text="""
CANARA BANK
Branch: VIKASPURI IFSC: CNRB0000125
Name: KAVITA RANI
A/c No: 00000099990000222
Nominee: DINESH KUMAR
Date Particulars Withdrawal Deposit Balance
01-05-2026 BALANCE B/F 5,000.00
28-05-2026 PMJJBY PREMIUM 43600 4,564.00
30-05-2026 PMSBY PREM 2000 4,544.00
""",
        transactions=(
            txn("2026-05-28", "PMJJBY PREMIUM", 436),
            txn("2026-05-30", "PMSBY PREM", 20),
        ),
        account_holder="Kavita Rani",
        bank="Canara Bank",
        branch="VIKASPURI",
        ifsc="CNRB0000125",
        account_last4="0222",
        nominee_name="Dinesh Kumar",
    ),
    Sample(
        name="bob_extra_spaces_inside_numbers",
        text="""
BANK OF BARODA
Branch: UTTAM NAGAR IFSC: BARB0TEST03
Name: RAJ KUMARI
A/c No: 00000012341234566
Nominee: MOHAN LAL
Date Particulars Withdrawal Deposit Balance
01-05-2026 BALANCE B/F 5,000.00
28-05-2026 PMJJBY PREMIUM 4 36.00 4,5 64.00
""",
        transactions=(txn("2026-05-28", "PMJJBY PREMIUM", 436),),
        account_holder="Raj Kumari",
        bank="Bank of Baroda",
        branch="UTTAM NAGAR",
        ifsc="BARB0TEST03",
        account_last4="4566",
        nominee_name="Mohan Lal",
    ),
    Sample(
        name="sbi_stray_column_pipes",
        text="""
| STATE BANK OF INDIA |
| Branch: DWARKA SECTOR 12 | IFSC: SBIN0000005 |
| Name: ANJU DEVI |
| A/c No: 00000023456789012 |
| Nominee: KAMLA DEVI |
| Date | Particulars | Withdrawal | Deposit | Balance |
| 01.05.2026 | BALANCE B/F | | | 5,000.00 |
| 28.05.2026 | PMJJBY PREMIUM | 436.00 | | 4,564.00 |
| 30.05.2026 | PMSBY PREM | 20.00; | | 4,544.00 |
""",
        transactions=(
            txn("2026-05-28", "PMJJBY PREMIUM", 436),
            txn("2026-05-30", "PMSBY PREM", 20),
        ),
        account_holder="Anju Devi",
        bank="SBI",
        branch="DWARKA SECTOR 12",
        ifsc="SBIN0000005",
        account_last4="9012",
        nominee_name="Kamla Devi",
    ),
    Sample(
        name="pnb_page_break_and_forward_balances",
        text="""
PUNJAB NATIONAL BANK
Branch: KALKAJI IFSC: PUNB0111103
Name: RAJENDRA PRASAD
A/c No: 00000034567890123
Nominee: SUSHMA DEVI
Date Particulars Withdrawal Deposit Balance
01-05-2026 BALANCE B/F 10,000.00
28-05-2026 PMJJBY PREMIUM 436.00 9,564.00
--------------------------------------------
PUNJAB NATIONAL BANK
Page 1 of 2
30-05-2026 PMSBY PREM 20.00 9,544.00
31-05-2026 CARRIED FORWARD 9,544.00
Page 2 of 2
Date Particulars Withdrawal Deposit Balance
01-06-2026 BROUGHT FORWARD 9,544.00
03-06-2026 BY CASH 2,000.00 11,544.00
""",
        transactions=(
            txn("2026-05-28", "PMJJBY PREMIUM", 436),
            txn("2026-05-30", "PMSBY PREM", 20),
            txn("2026-06-03", "BY CASH", 2000, "credit"),
        ),
        account_holder="Rajendra Prasad",
        bank="PNB",
        branch="KALKAJI",
        ifsc="PUNB0111103",
        account_last4="0123",
        nominee_name="Sushma Devi",
    ),
    Sample(
        name="canara_indian_digit_grouping",
        text="""
CANARA BANK
Branch: SECTOR 12 DWARKA IFSC: CNRB0000126
Name: SHYAM SUNDAR
A/c No: 00000045678901234
Nominee: LAXMI DEVI
Date Particulars Withdrawal Deposit Balance
01-05-2026 BALANCE B/F 1,23,456.00
28-05-2026 PMJJBY PREMIUM 436.00 1,23,020.00
07-06-2026 BY NEFT CR 1,00,000.00 2,23,020.00
""",
        transactions=(
            txn("2026-05-28", "PMJJBY PREMIUM", 436),
            txn("2026-06-07", "BY NEFT CR", 100000, "credit"),
        ),
        account_holder="Shyam Sundar",
        bank="Canara Bank",
        branch="SECTOR 12 DWARKA",
        ifsc="CNRB0000126",
        account_last4="1234",
        nominee_name="Laxmi Devi",
    ),
    Sample(
        name="cooperative_serial_number_column",
        text="""
THE NAVODAYA COOPERATIVE BANK LTD
Branch: UTTAM NAGAR IFSC: HDFC0TEST04
Name: JAGDISH PRASAD
A/c No: 00000056789012345
Nominee: SHANTI DEVI
Sr  Date        Particulars            Debit      Credit     Balance
1   01-05-2026  BALANCE B/F                                    1,000.00
2   28-05-2026  PMJJBY PREMIUM          436.00                 564.00
3   29-05-2026  BY CASH                            2,000.00    2,564.00
""",
        transactions=(
            txn("2026-05-28", "PMJJBY PREMIUM", 436),
            txn("2026-05-29", "BY CASH", 2000, "credit"),
        ),
        account_holder="Jagdish Prasad",
        branch="UTTAM NAGAR",
        ifsc="HDFC0TEST04",
        account_last4="2345",
        nominee_name="Shanti Devi",
    ),
    Sample(
        name="canara_deposit_column_before_withdrawal",
        text="""
CANARA BANK
Branch: TILAK NAGAR IFSC: CNRB0000127
Name: SUDHA RANI
A/c No: 00000078901234567
Nominee: ARJUN SINGH
Date        Particulars                     Deposit        Withdrawal     Balance
28-05-2026  PMJJBY PREMIUM                                 436.00         1,564.00
29-05-2026  BY CASH                           500.00                       2,064.00
""",
        transactions=(
            txn("2026-05-28", "PMJJBY PREMIUM", 436),
            txn("2026-05-29", "BY CASH", 500, "credit"),
        ),
        account_holder="Sudha Rani",
        bank="Canara Bank",
        branch="TILAK NAGAR",
        ifsc="CNRB0000127",
        account_last4="4567",
        nominee_name="Arjun Singh",
    ),
    Sample(
        name="union_bank_direction_cannot_be_read",
        text="""
UNION BANK OF INDIA
Branch: BHAJANPURA IFSC: UBIN0550004
Name: OM PRAKASH
A/c No: 00000067890123456
Nominee: SHANTI DEVI
Date Particulars Amount Balance
28-05-2026 MISC ENTRY 500.00 1,500.00
""",
        transactions=(txn("2026-05-28", "MISC ENTRY", 500, None),),
        account_holder="Om Prakash",
        bank="Union Bank of India",
        branch="BHAJANPURA",
        ifsc="UBIN0550004",
        account_last4="3456",
        nominee_name="Shanti Devi",
    ),
)

AMBIGUOUS = {
    "union_bank_direction_cannot_be_read": (
        "no opening balance, no Dr/Cr marker, no withdrawal/deposit header and a narration "
        "that says nothing either way: nothing on the row can tell a debit from a credit"
    ),
}
