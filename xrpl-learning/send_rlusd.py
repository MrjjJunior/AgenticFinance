import xrpl
from xrpl.clients import JsonRpcClient
from xrpl.wallet import Wallet
from xrpl.models.transactions import Payment
from xrpl.models.amounts import IssuedCurrencyAmount
from xrpl.transaction import submit_and_wait

def main():
    client = JsonRpcClient("https://s.altnet.rippletest.net:51234/")
    
    RLUSD_HEX = "524C555344000000000000000000000000000000"
    RLUSD_ISSUER = "rQhWct2fv4Vc4KRjRgMrxa8xPN9Zx9iLKV"

    # Recreate your funded wallet using the seed from Script 1
    SENDER_SEED = "sEdTfZPZNc187DTLNne8WxXHhDxFSQQ"  # Replace with your actual seed
    sender_wallet = Wallet.from_seed(SENDER_SEED)
    
    # The destination MUST already have an RLUSD trust line
    DESTINATION_ADDRESS = "rf13SEGB8jaymmi75i8BTrSj8ERwvWs2hW" # Replace with the receiving wallet's address

    # Instead of an integer of drops, we pass an IssuedCurrencyAmount
    payment_tx = Payment(
        account=sender_wallet.classic_address,
        amount=IssuedCurrencyAmount(
            currency=RLUSD_HEX,
            issuer=RLUSD_ISSUER,
            value="50.00"  # Send 50 RLUSD
        ),
        destination=DESTINATION_ADDRESS
    )

    print("Sending RLUSD payment...")
    try:
        response = submit_and_wait(payment_tx, client, sender_wallet)
        print(f"Result: {response.result['meta']['TransactionResult']}")
        print(f"Explorer: https://testnet.xrpl.org/transactions/{response.result['hash']}")
    except Exception as e:
        print(f"Transaction failed: {e}")

if __name__ == "__main__":
    main()