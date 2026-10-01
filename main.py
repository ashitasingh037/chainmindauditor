import os
import requests
from dotenv import load_dotenv
from web3 import Web3


# ============================================================
# SETUP
# ============================================================

load_dotenv()

ALCHEMY_URL = os.getenv("ALCHEMY_URL")

if not ALCHEMY_URL:
    print("❌ ALCHEMY_URL not found in .env")
    exit()

w3 = Web3(Web3.HTTPProvider(ALCHEMY_URL))


# ============================================================
# CONNECTION
# ============================================================

print("=" * 60)
print("                 CHAIN-MIND AUDITOR")
print("=" * 60)
print()

if not w3.is_connected():
    print("❌ Could not connect to Ethereum Sepolia.")
    exit()

latest_block_number = w3.eth.block_number

print("✅ Connected to Ethereum Sepolia!")
print("Latest block:", latest_block_number)
print()


# ============================================================
# SETTINGS
# ============================================================

BLOCKS_TO_CHECK = 5

start_block = latest_block_number - BLOCKS_TO_CHECK + 1

print("Auditing blocks...")
print(f"From block: {start_block}")
print(f"To block:   {latest_block_number}")
print()


# ============================================================
# STEP 1 — GET TRANSACTIONS
# ============================================================

all_transactions = []

for block_number in range(start_block, latest_block_number + 1):

    print(f"📦 Reading block {block_number}...")

    try:
        block = w3.eth.get_block(
            block_number,
            full_transactions=True
        )

        transactions = block.transactions

        print(f"   Transactions: {len(transactions)}")

        for tx in transactions:
            all_transactions.append(tx)

    except Exception as e:
        print(f"❌ Error reading block {block_number}: {e}")


print()
print(f"Total transactions collected: {len(all_transactions)}")
print()


# ============================================================
# STEP 2 — COLLECT UNIQUE DESTINATION ADDRESSES
# ============================================================

addresses = set()

for tx in all_transactions:

    to_address = tx["to"]

    if to_address is not None:
        addresses.add(to_address.lower())


print(f"Unique destination addresses: {len(addresses)}")
print()


# ============================================================
# STEP 3 — CHECK CONTRACTS IN BATCHES
# ============================================================

print("🔍 Checking which addresses are smart contracts...")

contract_addresses = set()

addresses = list(addresses)

BATCH_SIZE = 50

for i in range(0, len(addresses), BATCH_SIZE):

    batch = addresses[i:i + BATCH_SIZE]

    requests_data = []

    for request_id, address in enumerate(batch):

        requests_data.append({
            "jsonrpc": "2.0",
            "id": request_id,
            "method": "eth_getCode",
            "params": [
                address,
                hex(latest_block_number)
            ]
        })

    try:

        response = requests.post(
            ALCHEMY_URL,
            json=requests_data,
            timeout=15
        )

        response.raise_for_status()

        results = response.json()

        for result in results:

            code = result.get("result", "0x")

            if code != "0x" and code != "0x0":

                request_id = result["id"]

                if request_id < len(batch):

                    contract_addresses.add(
                        batch[request_id]
                    )

    except Exception as e:

        print(f"⚠️ Batch check failed: {e}")


print(
    f"Smart contracts detected: {len(contract_addresses)}"
)

print()


# ============================================================
# STEP 4 — AUDIT TRANSACTIONS
# ============================================================

high_value_transactions = 0
zero_value_transactions = 0
contract_interactions = 0
flagged_transactions = 0


print("=" * 60)
print("                    AUDITING")
print("=" * 60)
print()


for tx in all_transactions:

    tx_hash = tx["hash"].hex()

    from_address = tx["from"]

    to_address = tx["to"]

    value_eth = float(
        w3.from_wei(tx["value"], "ether")
    )

    reasons = []

    # --------------------------------------------------------
    # HIGH VALUE
    # --------------------------------------------------------

    if value_eth >= 0.01:

        high_value_transactions += 1

        reasons.append("HIGH VALUE")


    # --------------------------------------------------------
    # ZERO VALUE
    # --------------------------------------------------------

    if value_eth == 0:

        zero_value_transactions += 1

        reasons.append("ZERO VALUE")


    # --------------------------------------------------------
    # CONTRACT INTERACTION
    # --------------------------------------------------------

    if (
        to_address is not None
        and to_address.lower() in contract_addresses
    ):

        contract_interactions += 1

        reasons.append("CONTRACT INTERACTION")


    # --------------------------------------------------------
    # FLAG
    # --------------------------------------------------------

    if value_eth >= 0.01:

        flagged_transactions += 1

        print("⚠️ FLAGGED TRANSACTION")
        print("-" * 60)

        print("Transaction:", tx_hash)
        print("From:", from_address)
        print("To:", to_address)
        print("Value:", value_eth, "ETH")
        print("Reason:", ", ".join(reasons))

        print()


# ============================================================
# AUDIT SUMMARY
# ============================================================

print("=" * 60)
print("                    AUDIT SUMMARY")
print("=" * 60)

print()

print(
    f"Blocks checked:           {BLOCKS_TO_CHECK}"
)

print(
    f"Transactions checked:    {len(all_transactions)}"
)

print()

print(
    f"High-value transactions: {high_value_transactions}"
)

print(
    f"Zero-value transactions: {zero_value_transactions}"
)

print(
    f"Smart contracts found:   {len(contract_addresses)}"
)

print(
    f"Contract interactions:   {contract_interactions}"
)

print()

print(
    f"Transactions flagged:    {flagged_transactions}"
)

print()
print("=" * 60)

if flagged_transactions > 0:

    print("⚠️ Some transactions require review.")

else:

    print("✅ No suspicious transactions detected.")

print("=" * 60)

print()
print("✅ Audit complete.")