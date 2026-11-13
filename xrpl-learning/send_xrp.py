import xrpl
from xrpl.clients import JsonRpcClient
from xrpl.wallet import generate_faucet_wallet
from xrpl.models.transactions import Payment
from xrpl.transaction import submit_and_wait

def main():
    # 1. Connect to XRPL Testnet
    client = JsonRpcClient("https://s.altnet.rippletest.net:51234/")
    print("Connected to XRPL Testnet.")

    # 2. Create and fund two test wallets
    print("Funding sender wallet...")
    sender = generate_faucet_wallet(client, debug=True)
    
    print("Funding receiver wallet...")
    receiver = generate_faucet_wallet(client, debug=True)

    print(f"\nSender Address: {sender.classic_address}")
    print(f"Receiver Address: {receiver.classic_address}")

    # 3. Prepare the payment (Amounts in XRPL are in 'drops', 1 XRP = 1,000,000 drops)
    payment = Payment(
        account=sender.classic_address,
        amount=xrpl.utils.xrp_to_drops(1),
        destination=receiver.classic_address,
    )

    print("\nSigning and submitting transaction...")
    
    # 4. Sign, submit, and wait for validation on the ledger
    try:
        response = submit_and_wait(payment, client, sender)
        
        # 5. Output the results
        print(f"\nTransaction result: {response.result['meta']['TransactionResult']}")
        print(f"Transaction hash: {response.result['hash']}")
        print(f"View on explorer: https://testnet.xrpl.org/transactions/{response.result['hash']}")
    
    except xrpl.transaction.XRPLReliableSubmissionException as e:
        print(f"Transaction failed: {e}")

if __name__ == "__main__":
    main()