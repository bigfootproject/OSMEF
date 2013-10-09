import json
import logging
log = logging.getLogger()

from osmef.scenario import AvailableScenarios


def parse(filename):
    config = json.load(open(filename, "r"))
    scenario = {}
    for runner in config:
        measure = config[runner]["measure"]
        if measure in AvailableScenarios:
            scenario[runner] = AvailableScenarios[measure](config[runner])
        else:
            log.error("Unknown scenario {0} found in file {1}".format(measure, filename))
    return scenario


def export(filename, scenario_description):
    json.dump(scenario_description, open(filename, "w"))
