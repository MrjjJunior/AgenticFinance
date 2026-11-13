import xrpl
from xrpl.clients import JsonRpcClient
from xrpl.wallet import generate_faucet_wallet
from xrpl.models.transactions import TrustSet
from xrpl.models.amounts import IssuedCurrencyAmount
from xrpl.transaction import submit_and_wait

def main():
    client = JsonRpcClient("https://s.altnet.rippletest.net:51234/")
    
    # Official Testnet RLUSD details
    RLUSD_HEX = "524C555344000000000000000000000000000000"
    RLUSD_ISSUER = "rQhWct2fv4Vc4KRjRgMrxa8xPN9Zx9iLKV"

    print("Funding a new wallet...")
    wallet = generate_faucet_wallet(client, debug=True)
    print(f"Wallet Address: {wallet.classic_address}")
    print(f"Wallet Seed: {wallet.seed}\n")

    # The TrustSet transaction authorises the issuer
    trust_set_tx = TrustSet(
        account=wallet.classic_address,
        limit_amount=IssuedCurrencyAmount(
            currency=RLUSD_HEX,
            issuer=RLUSD_ISSUER,
            value="1000000"  # The maximum amount of RLUSD you are willing to hold
        )
    )

    print("Submitting Trust Line transaction...")
    response = submit_and_wait(trust_set_tx, client, wallet)
    
    print(f"Result: {response.result['meta']['TransactionResult']}")
    print(f"Explorer: https://testnet.xrpl.org/transactions/{response.result['hash']}")
    print("\nNext step: Copy your Wallet Address and visit https://tryrlusd.com/ to fund it with RLUSD.")

if __name__ == "__main__":
    main()