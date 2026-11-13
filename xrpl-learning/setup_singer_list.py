import xrpl
from xrpl.clients import JsonRpcClient
from xrpl.wallet import generate_faucet_wallet
from xrpl.models.transactions import SignerListSet, SignerEntry
from xrpl.models.transactions.account_set import AccountSet, AccountSetAsfFlag
from xrpl.transaction import submit_and_wait

def main():
    client = JsonRpcClient("https://s.altnet.rippletest.net:51234/")
    
    # 1. Generate the member's main account (the one holding the funds)
    print("Funding main member account...")
    main_wallet = generate_faucet_wallet(client, debug=True)
    print(f"Main Account: {main_wallet.classic_address}")

    # 2. In a real app, these addresses come from the phone's secure enclave (Human) 
    # and your backend services (Agent and Co-signer). We generate them here for testing.
    human_wallet = xrpl.wallet.Wallet.create()
    agent_wallet = xrpl.wallet.Wallet.create()
    policy_cosigner_wallet = xrpl.wallet.Wallet.create()

    print(f"\nHuman Address: {human_wallet.classic_address} | seed: {human_wallet.seed}")
    print(f"Agent Address: {agent_wallet.classic_address} | seed: {agent_wallet.seed}")
    print(f"Policy Co-signer Address: {policy_cosigner_wallet.classic_address} | seed: {policy_cosigner_wallet.seed}\n")

    # 3. Create the SignerListSet transaction
    signer_list_tx = SignerListSet(
        account=main_wallet.classic_address,
        signer_quorum=2,
        signer_entries=[
            SignerEntry(account=human_wallet.classic_address, signer_weight=2),
            SignerEntry(account=agent_wallet.classic_address, signer_weight=1),
            SignerEntry(account=policy_cosigner_wallet.classic_address, signer_weight=1),
        ]
    )

    print("Submitting SignerListSet transaction...")
    response_signer = submit_and_wait(signer_list_tx, client, main_wallet)
    print(f"Signer List Result: {response_signer.result['meta']['TransactionResult']}")

    # 4. Disable the Master Key so ONLY the Signer List can be used
    print("\nDisabling Master Key...")
    disable_master_tx = AccountSet(
        account=main_wallet.classic_address,
        set_flag=AccountSetAsfFlag.ASF_DISABLE_MASTER
    )
    
    response_disable = submit_and_wait(disable_master_tx, client, main_wallet)
    print(f"Disable Master Key Result: {response_disable.result['meta']['TransactionResult']}")
    
    print("\nSuccess! The agent can now only transact if the policy co-signer also signs.")

if __name__ == "__main__":
    main()