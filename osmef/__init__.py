import logging
_log = logging.getLogger(__name__)

import osmef.command_protocol

__version__ = "0.2"


def deploy(scenario):
    runners = {}
    for runner in scenario:
        pr = osmef.command_protocol.OSMeFRunner(runner)
        runners[runner] = pr
        _log.info("Initializing scenario on runner {0}".format(runner))
        scenario[runner].init(pr)
    _log.info("Scenario deployment completed")
    return runners


def run(runners, scenario):
    _log.info("Scenario running...")
    _log.info("Scenario run completed")


def end(runners, scenario):
    for runner in scenario:
        scenario[runner].end(runners[runner])
        runners[runner].quit()
    _log.info("Cleanup completed")

