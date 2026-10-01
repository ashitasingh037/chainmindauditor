import os
from web3 import Web3
from dotenv import load_dotenv



load_dotenv()

ALCHEMY_URL = os.getenv("ALCHEMY_URL")

if not ALCHEMY_URL:
    print("❌ ALCHEMY_URL not found in .env")
    exit()

w3 = Web3(Web3.HTTPProvider(ALCHEMY_URL))

if not w3.is_connected():
    print("❌ Could not connect to Ethereum Sepolia")
    exit()

print("✅ Connected to Ethereum Sepolia!")



latest_block = w3.eth.block_number

print(f"Latest block: {latest_block}")

BLOCKS_TO_CHECK = 5

start_block = latest_block - BLOCKS_TO_CHECK + 1

print(f"Auditing blocks {start_block} → {latest_block}")
print("=" * 70)


total_transactions = 0
high_value_transactions = 0
zero_value_transactions = 0
contract_interactions = 0
flagged_transactions = 0



for block_number in range(start_block, latest_block + 1):

    print(f"\n📦 Checking block {block_number}...")

    try:
        block = w3.eth.get_block(
            block_number,
            full_transactions=True
        )
    except Exception as e:
        print(f"❌ Could not read block: {e}")
        continue

    transactions = block["transactions"]

    print(f"Transactions: {len(transactions)}")

    
    
    for tx in transactions:

        total_transactions += 1

        tx_hash = tx["hash"].hex()

        from_address = tx["from"]
        to_address = tx["to"]

        value_eth = float(
            w3.from_wei(tx["value"], "ether")
        )

        
        
        high_value = value_eth >= 0.01

        if high_value:
            high_value_transactions += 1

        
        
        zero_value = value_eth == 0

        if zero_value:
            zero_value_transactions += 1

       
       
        contract_call = (
            to_address is not None
            and len(tx["input"]) > 2
        )

        if contract_call:
            contract_interactions += 1

        
        
        reasons = []

        if high_value:
            reasons.append("HIGH VALUE")

        # We flag contract interactions separately only
        # when they also have significant value.
        if contract_call and high_value:
            reasons.append("CONTRACT + HIGH VALUE")

        if reasons:

            flagged_transactions += 1

            # Print only flagged transactions
            print("\n⚠️ FLAGGED TRANSACTION")
            print("-" * 60)
            print(f"Transaction: {tx_hash}")
            print(f"From: {from_address}")
            print(f"To: {to_address}")
            print(f"Value: {value_eth} ETH")
            print(f"Reason: {', '.join(reasons)}")




print("\n")
print("=" * 70)
print("                       AUDIT SUMMARY")
print("=" * 70)

print(f"Blocks checked:             {BLOCKS_TO_CHECK}")
print(f"Transactions checked:      {total_transactions}")
print()
print(f"High-value transactions:   {high_value_transactions}")
print(f"Zero-value transactions:   {zero_value_transactions}")
print(f"Contract interactions:     {contract_interactions}")
print()
print(f"Transactions flagged:      {flagged_transactions}")

print("=" * 70)

if flagged_transactions > 0:
    print("⚠️ Some transactions require review.")
else:
    print("✅ No transactions were flagged.")

print("=" * 70)
