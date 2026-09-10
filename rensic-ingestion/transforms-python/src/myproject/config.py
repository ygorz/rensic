"""
Rensic Ingestion — Configuration Module
========================================

Centralized configuration for the multi-chain RPC ingestion pipeline.
Supports curated mainnets: Ethereum, Base, Arbitrum, Polygon, Optimism, BSC, Robinhood Chain, Avalanche.

Each chain has its own:
  - Alchemy-compatible RPC hostname
  - Native token symbol and decimals
  - Block explorer URL pattern
  - Supported transfer categories
  - Any chain-specific quirks
"""
from dataclasses import dataclass, field
from typing import List, Optional


# ============================================================================
# CHAIN REGISTRY — Full multi-chain configuration
# ============================================================================

@dataclass(frozen=True)
class ChainConfig:
    """Configuration for a single EVM chain."""
    chain_id: str                    # Internal identifier (e.g., "ethereum")
    display_name: str                # Human-readable name
    alchemy_subdomain: str           # Alchemy subdomain (e.g., "eth-mainnet")
    native_symbol: str               # Native token symbol (e.g., "ETH")
    native_decimals: int             # Native token decimals (usually 18)
    evm_chain_id: int                # Numeric EVM chain ID (e.g., 1 for Ethereum)
    explorer_url: str                # Block explorer base URL
    explorer_tx_path: str            # Path pattern for transaction links
    explorer_address_path: str       # Path pattern for address links
    supported_categories: List[str] = field(default_factory=lambda: [
        "external", "internal", "erc20", "erc721", "erc1155"
    ])
    # Chain-specific quirks
    supports_internal_transfers: bool = True
    supports_erc1155: bool = True
    max_block_range: Optional[int] = None  # Some chains limit block range queries
    # alchemy_getAssetTransfers fromBlock window. ETH ~12s, L2s ~2s.
    blocks_per_day: int = 7200


# Full chain registry — curated eight mainnets only
CHAINS: dict = {
    "ethereum": ChainConfig(
        chain_id="ethereum",
        display_name="Ethereum Mainnet",
        alchemy_subdomain="eth-mainnet",
        native_symbol="ETH",
        native_decimals=18,
        evm_chain_id=1,
        explorer_url="https://etherscan.io",
        explorer_tx_path="/tx/{tx_hash}",
        explorer_address_path="/address/{address}",
    ),
    "base": ChainConfig(
        chain_id="base",
        display_name="Base",
        alchemy_subdomain="base-mainnet",
        native_symbol="ETH",
        native_decimals=18,
        evm_chain_id=8453,
        explorer_url="https://basescan.org",
        explorer_tx_path="/tx/{tx_hash}",
        explorer_address_path="/address/{address}",
        blocks_per_day=43200,
    ),
    "arbitrum": ChainConfig(
        chain_id="arbitrum",
        display_name="Arbitrum One",
        alchemy_subdomain="arb-mainnet",
        native_symbol="ETH",
        native_decimals=18,
        evm_chain_id=42161,
        explorer_url="https://arbiscan.io",
        explorer_tx_path="/tx/{tx_hash}",
        explorer_address_path="/address/{address}",
        blocks_per_day=43200,
    ),
    "polygon": ChainConfig(
        chain_id="polygon",
        display_name="Polygon PoS",
        alchemy_subdomain="polygon-mainnet",
        native_symbol="MATIC",
        native_decimals=18,
        evm_chain_id=137,
        explorer_url="https://polygonscan.com",
        explorer_tx_path="/tx/{tx_hash}",
        explorer_address_path="/address/{address}",
        blocks_per_day=43200,
    ),
    "optimism": ChainConfig(
        chain_id="optimism",
        display_name="Optimism",
        alchemy_subdomain="opt-mainnet",
        native_symbol="ETH",
        native_decimals=18,
        evm_chain_id=10,
        explorer_url="https://optimistic.etherscan.io",
        explorer_tx_path="/tx/{tx_hash}",
        explorer_address_path="/address/{address}",
        blocks_per_day=43200,
    ),
    "bsc": ChainConfig(
        chain_id="bsc",
        display_name="BNB Smart Chain",
        alchemy_subdomain="bnb-mainnet",
        native_symbol="BNB",
        native_decimals=18,
        evm_chain_id=56,
        explorer_url="https://bscscan.com",
        explorer_tx_path="/tx/{tx_hash}",
        explorer_address_path="/address/{address}",
        blocks_per_day=28800,
    ),
    "robinhood": ChainConfig(
        chain_id="robinhood",
        display_name="Robinhood Chain",
        alchemy_subdomain="robinhood-mainnet",
        native_symbol="ETH",
        native_decimals=18,
        evm_chain_id=4663,
        explorer_url="https://robinhoodchain.blockscout.com",
        explorer_tx_path="/tx/{tx_hash}",
        explorer_address_path="/address/{address}",
        # RH Chain ~0.1s blocks (Arbitrum L2); ~864000 blocks/day.
        blocks_per_day=864000,
    ),
    "avalanche": ChainConfig(
        chain_id="avalanche",
        display_name="Avalanche C-Chain",
        alchemy_subdomain="avax-mainnet",
        native_symbol="AVAX",
        native_decimals=18,
        evm_chain_id=43114,
        explorer_url="https://snowtrace.io",
        explorer_tx_path="/tx/{tx_hash}",
        explorer_address_path="/address/{address}",
        blocks_per_day=28800,
    ),
}


def get_alchemy_url(chain_id: str, api_key: str) -> str:
    """
    Build the full Alchemy RPC URL for a given chain.
    Pattern: https://{subdomain}.g.alchemy.com/v2/{api_key}
    """
    chain = CHAINS.get(chain_id)
    if not chain:
        raise ValueError(f"Unknown chain: {chain_id}. Available: {list(CHAINS.keys())}")
    return f"https://{chain.alchemy_subdomain}.g.alchemy.com/v2/{api_key}"


def get_explorer_tx_url(chain_id: str, tx_hash: str) -> str:
    """Build a block explorer URL for a transaction."""
    chain = CHAINS.get(chain_id)
    if not chain:
        return f"https://etherscan.io/tx/{tx_hash}"
    return chain.explorer_url + chain.explorer_tx_path.format(tx_hash=tx_hash)


def get_explorer_address_url(chain_id: str, address: str) -> str:
    """Build a block explorer URL for an address."""
    chain = CHAINS.get(chain_id)
    if not chain:
        return f"https://etherscan.io/address/{address}"
    return chain.explorer_url + chain.explorer_address_path.format(address=address)


def get_transfer_categories(chain_id: str) -> list:
    """Get supported transfer categories for a chain (handles chain-specific quirks)."""
    chain = CHAINS.get(chain_id)
    if not chain:
        return ["external", "erc20"]
    categories = list(chain.supported_categories)
    if not chain.supports_internal_transfers:
        categories = [c for c in categories if c != "internal"]
    if not chain.supports_erc1155:
        categories = [c for c in categories if c != "erc1155"]
    return categories


# ============================================================================
# PIPELINE PARAMETERS
# ============================================================================

# Default lookback window in days (desk demo default is 30; cap is 365)
DEFAULT_LOOKBACK_DAYS = 30

# Maximum transfers per API page (Alchemy default)
MAX_RESULTS_PER_PAGE = 1000

# Maximum pages to fetch per address per chain (safety limit)
MAX_PAGES_PER_REQUEST = 100

# Transfer categories (default set for Alchemy API)
TRANSFER_CATEGORIES = ["external", "internal", "erc20", "erc721", "erc1155"]


# ============================================================================
# CROSS-CHAIN CORRELATION
# ============================================================================

def extract_hex_address(composite_id: str) -> str:
    """
    Extract the raw hex address from a composite ID (chain:0xAddress).
    Used for cross-chain correlation (same wallet on multiple chains).
    """
    parts = composite_id.split(":", 1)
    return parts[1] if len(parts) == 2 else composite_id


def is_same_wallet(address_id_1: str, address_id_2: str) -> bool:
    """
    Check if two composite address IDs represent the same wallet
    (same hex address, different chains). True for EOAs, may not hold for contracts.
    """
    hex1 = extract_hex_address(address_id_1)
    hex2 = extract_hex_address(address_id_2)
    return hex1.lower() == hex2.lower()


# ============================================================================
# COMPOSITE KEY HELPERS
# ============================================================================

def make_address_id(chain_id: str, address: str) -> str:
    """Create composite address primary key: chain:0xAddress (lowercased)."""
    return f"{chain_id}:{address.lower()}"


def make_transaction_id(chain_id: str, tx_hash: str) -> str:
    """Create composite transaction primary key: chain:0xTxHash."""
    return f"{chain_id}:{tx_hash.lower()}"


def make_transfer_id(chain_id: str, tx_hash: str, log_index: int) -> str:
    """Create composite transfer primary key: chain:0xTxHash:logIndex."""
    return f"{chain_id}:{tx_hash.lower()}:{log_index}"



# Demo queue used live-case-001; ontology Investigation Case PK is this UUID.
LEGACY_PIPELINE_CASE_IDS = {
    "live-case-001": "3cf7174a-fcf2-494c-b4bc-16c66fc6ea6f",
}


def remap_pipeline_case_id(frame):
    """Map leftover pipeline case ids onto ontology Investigation Case PKs."""
    import polars as pl
    schema_names = frame.collect_schema().names() if hasattr(frame, "collect_schema") else frame.columns
    if "case_id" not in schema_names:
        return frame
    return frame.with_columns(pl.col("case_id").replace(LEGACY_PIPELINE_CASE_IDS))


def make_interaction_id(chain_id: str, tx_hash: str, trace_index: int) -> str:
    """Create composite interaction primary key: chain:0xTxHash:traceIndex."""
    return f"{chain_id}:{tx_hash.lower()}:{trace_index}"
