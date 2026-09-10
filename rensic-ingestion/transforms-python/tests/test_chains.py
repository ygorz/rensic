from myproject.config import CHAINS, get_alchemy_url, get_explorer_address_url

EXPECTED = {
    "ethereum",
    "base",
    "arbitrum",
    "polygon",
    "optimism",
    "bsc",
    "robinhood",
    "avalanche",
}


def test_chains_registry_ids():
    assert set(CHAINS.keys()) == EXPECTED


def test_alchemy_subdomains_standard():
    assert CHAINS["bsc"].alchemy_subdomain == "bnb-mainnet"
    assert CHAINS["robinhood"].alchemy_subdomain == "robinhood-mainnet"
    assert CHAINS["avalanche"].alchemy_subdomain == "avax-mainnet"
    assert CHAINS["robinhood"].evm_chain_id == 4663
    assert CHAINS["bsc"].evm_chain_id == 56
    assert CHAINS["avalanche"].evm_chain_id == 43114
    assert CHAINS["bsc"].blocks_per_day == 28800
    assert CHAINS["avalanche"].blocks_per_day == 28800
    assert CHAINS["robinhood"].blocks_per_day == 864000
    url = get_alchemy_url("robinhood", "KEY")
    assert url == "https://robinhood-mainnet.g.alchemy.com/v2/KEY"


def test_explorer_urls():
    assert get_explorer_address_url("bsc", "0xabc").startswith("https://bscscan.com/")
    assert get_explorer_address_url("robinhood", "0xabc").startswith(
        "https://robinhoodchain.blockscout.com/"
    )
    assert get_explorer_address_url("avalanche", "0xabc").startswith("https://snowtrace.io/")
