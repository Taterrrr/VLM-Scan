import json

def compare_payment(filepath: str, database: str):
    with str(filepath), "r" as f:
        filejson = json.load(f)

    with str(database), "r" as f:
        databason = json.load(f)

    claimbook = filejson["claims"]  #claimbook is list of claim dicts
    for claim in claimbook: #each claim is a dict
        cnum = claim["claim_number"]
        codebook = claim["ada_codes"] #codebook is a list of dicts
        for code in codebook:
            dcode = code["alphanumeric_code"]
            amtpaid= code["amount_paid"]
            ###NOW COMPARE AMT PAID TO THE PROPER AMT BY CODE###


        

    