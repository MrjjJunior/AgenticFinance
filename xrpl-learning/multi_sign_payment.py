import xrpl
from xrpl.clients import JsonRpcClient
from xrpl.wallet import Wallet
from xrpl.models.transactions import Payment
from xrpl.transaction import autofill, sign, multisign, submit_and_wait

def main():
    client = JsonRpcClient("https://s.altnet.rippletest.net:51234/")
    
    # 1. Define the main account (the one you disabled the master key on)
    human_wallet = xrpl.wallet.Wallet.create()
    agent_wallet = xrpl.wallet.Wallet.create()
    policy_cosigner_wallet = xrpl.wallet.Wallet.create()
    
    MAIN_ACCOUNT_ADDRESS = f"{human_wallet.classic_address}" 
    
    # 2. Load the signer wallets using their seeds
    AGENT_SEED = "sEd7G4nSPaiJDVx4B49WTXAfTkd9UEz"
    agent_wallet = Wallet.from_seed(AGENT_SEED)
    
    COSIGNER_SEED = "rLskAtV4wcq3MCA7YQtY11QKTuoH5wUjuW"
    cosigner_wallet = Wallet.from_seed(COSIGNER_SEED)
    
    DESTINATION_ADDRESS = "rDestinationAddressHere..."

    print("Preparing base transaction...")
    # 3. Create the base payment transaction. 
    # Note: The 'account' is the main member account, NOT the signers.
    payment = Payment(
        account=MAIN_ACCOUNT_ADDRESS,
        amount=xrpl.utils.xrp_to_drops(1),
        destination=DESTINATION_ADDRESS,
    )

    # 4. Autofill sequence and fees.
    # Multi-signed transactions cost more in fees. Passing signers_count 
    # ensures xrpl-py calculates the correct network fee automatically.
    autofilled_tx = autofill(payment, client, signers_count=2)

    print("Gathering signatures...")
    # 5. Each party signs the transaction independently.
    # multisign=True is crucial: it places the signature in the 'Signers' array 
    # instead of the main 'TxnSignature' field.
    tx_signed_by_agent = sign(autofilled_tx, agent_wallet, multisign=True)
    tx_signed_by_cosigner = sign(autofilled_tx, cosigner_wallet, multisign=True)

    print("Combining signatures...")
    # 6. Combine the individual signatures into one final transaction blob.
    combined_tx = multisign(autofilled_tx, [tx_signed_by_agent, tx_signed_by_cosigner])

    print("Submitting multi-signed transaction to the ledger...")
    # 7. Submit the assembled transaction.
    try:
        response = submit_and_wait(combined_tx, client)
        print(f"\nResult: {response.result['meta']['TransactionResult']}")
        print(f"Explorer: https://testnet.xrpl.org/transactions/{response.result['hash']}")
    except xrpl.transaction.XRPLReliableSubmissionException as e:
        print(f"Transaction failed: {e}")

if __name__ == "__main__":
    main()
