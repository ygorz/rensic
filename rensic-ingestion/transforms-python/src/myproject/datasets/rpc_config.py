"""
Rensic — RPC Chain Configuration Dataset
==========================================

Creates and maintains a user-editable configuration dataset that stores
RPC endpoint URLs and API keys for each supported chain.

Investigators can edit this dataset directly in Foundry to:
  - Add new chains
  - Update API keys
  - Enable/disable chains
  - Change RPC providers

No Data Connection setup required — just edit the rows.
"""
import polars as pl
from transforms.api import transform, Output


@transform.using(
    rpc_config=Output(
        "/George Gorzhiyev-a8216a/Rensic/data-integration/sources/rpc_chain_config"
    ),
)
def seed_rpc_config(rpc_config):
    """
    Seeds the RPC configuration with default Alchemy endpoints.

    Schema:
      chain_id         — Internal chain identifier (e.g., "ethereum")
      display_name     — Human-readable name (e.g., "Ethereum Mainnet")
      rpc_base_url     — Base URL without API key (e.g., "https://eth-mainnet.g.alchemy.com/v2/")
      api_key          — The RPC provider API key (user fills this in)
      enabled          — Whether this chain is active for ingestion
      native_symbol    — Native token symbol (e.g., "ETH", "MATIC")
      explorer_url     — Block explorer base URL for linking

    IMPORTANT: After first build, edit the dataset directly to add your API keys.
    Do NOT rebuild this transform — it will overwrite your edits.
    Use APPEND mode or just edit in the Foundry UI.
    """
    default_config = [
        {
            "chain_id": "ethereum",
            "display_name": "Ethereum Mainnet",
            "rpc_base_url": "https://eth-mainnet.g.alchemy.com/v2/",
            "api_key": "PASTE_YOUR_ALCHEMY_KEY_HERE",
            "enabled": True,
            "native_symbol": "ETH",
            "explorer_url": "https://etherscan.io",
        },
        {
            "chain_id": "base",
            "display_name": "Base",
            "rpc_base_url": "https://base-mainnet.g.alchemy.com/v2/",
            "api_key": "PASTE_YOUR_ALCHEMY_KEY_HERE",
            "enabled": False,
            "native_symbol": "ETH",
            "explorer_url": "https://basescan.org",
        },
        {
            "chain_id": "arbitrum",
            "display_name": "Arbitrum One",
            "rpc_base_url": "https://arb-mainnet.g.alchemy.com/v2/",
            "api_key": "PASTE_YOUR_ALCHEMY_KEY_HERE",
            "enabled": False,
            "native_symbol": "ETH",
            "explorer_url": "https://arbiscan.io",
        },
        {
            "chain_id": "polygon",
            "display_name": "Polygon PoS",
            "rpc_base_url": "https://polygon-mainnet.g.alchemy.com/v2/",
            "api_key": "PASTE_YOUR_ALCHEMY_KEY_HERE",
            "enabled": False,
            "native_symbol": "MATIC",
            "explorer_url": "https://polygonscan.com",
        },
        {
            "chain_id": "optimism",
            "display_name": "Optimism",
            "rpc_base_url": "https://opt-mainnet.g.alchemy.com/v2/",
            "api_key": "PASTE_YOUR_ALCHEMY_KEY_HERE",
            "enabled": False,
            "native_symbol": "ETH",
            "explorer_url": "https://optimistic.etherscan.io",
        },
        {
            "chain_id": "bsc",
            "display_name": "BNB Smart Chain",
            "rpc_base_url": "https://bnb-mainnet.g.alchemy.com/v2/",
            "api_key": "PASTE_YOUR_ALCHEMY_KEY_HERE",
            "enabled": False,
            "native_symbol": "BNB",
            "explorer_url": "https://bscscan.com",
        },
        {
            "chain_id": "robinhood",
            "display_name": "Robinhood Chain",
            "rpc_base_url": "https://robinhood-mainnet.g.alchemy.com/v2/",
            "api_key": "PASTE_YOUR_ALCHEMY_KEY_HERE",
            "enabled": False,
            "native_symbol": "ETH",
            "explorer_url": "https://robinhoodchain.blockscout.com",
        },
        {
            "chain_id": "avalanche",
            "display_name": "Avalanche C-Chain",
            "rpc_base_url": "https://avax-mainnet.g.alchemy.com/v2/",
            "api_key": "PASTE_YOUR_ALCHEMY_KEY_HERE",
            "enabled": False,
            "native_symbol": "AVAX",
            "explorer_url": "https://snowtrace.io",
        },
    ]

    rpc_config.write_table(pl.DataFrame(default_config))
