from osmef.scenario.base import NetBTCLocalhostScenario
from osmef.scenario.base import NetBTCScenario

AvailableScenarios = {
    'NetBTCLocalhost': NetBTCLocalhostScenario,
    'NetBTC': NetBTCScenario,
}

# runner types for the NetBTC scenario
BTC_SENDER = 1
BTC_RECEIVER = 2
