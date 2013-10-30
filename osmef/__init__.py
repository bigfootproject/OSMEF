import logging
_log = logging.getLogger(__name__)

__version__ = "0.2"


def deploy(scenario):
    for runner in scenario:
        _log.info("Spawning runner %s" % runner.name)
        runner.spawn()
    for runner in scenario:
        _log.info("Connecting to runner %s" % runner.name)
        runner.connect()
        _log.info("Initializing scenario on runner {0}".format(runner.name))
        runner.scenario_init()
    _log.info("Scenario deployment completed")


def run(scenario):
    results = {}
    _log.info("Scenario running...")
    for runner in scenario:
        runner.scenario_run()
    for runner in scenario:
        results[runner.name] = runner.scenario_get_results()
    _log.info("Scenario run completed")
    return results


def end(scenario):
    for runner in scenario:
        runner.scenario_end()
    _log.info("Cleanup completed")

