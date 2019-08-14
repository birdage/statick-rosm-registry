"""json reporting plugin unit tests."""
import argparse
import json
import os
import requests
import os
import random
from datetime import datetime
from yapsy.PluginManager import PluginManager

import statick_tool
from statick_tool.config import Config
from statick_tool.issue import Issue
from statick_tool.package import Package
from statick_tool.plugin_context import PluginContext
from statick_tool.plugins.reporting.rosm_registry_plugin.json_risk_assessment_reporting_plugin import \
    JSONRiskAssessmentReportingPlugin
from statick_tool.reporting_plugin import ReportingPlugin
from statick_tool.resources import Resources


def setup_json_reporting_plugin():
    """Create an instance of the xmllint plugin."""
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("output_directory")
    arg_parser.add_argument("--show-tool-output", dest="show_tool_output",
                            action="store_true", help="Show tool output")

    resources = Resources([os.path.join(os.path.dirname(statick_tool.__file__),
                                        'plugins')])
    config = Config(resources.get_file("config.yaml"))
    plugin_context = PluginContext(
        arg_parser.parse_args([os.getcwd()]), resources, config)
    jrarp = JSONRiskAssessmentReportingPlugin()
    jrarp.set_plugin_context(plugin_context)
    return jrarp


def test_json_reporting_plugin_found():
    """Test that the plugin manager finds the JSON plugin."""
    manager = PluginManager()
    # Get the path to statick_tool/__init__.py, get the directory part, and
    # add 'plugins' to that to get the standard plugins dir
    manager.setPluginPlaces([os.path.join(os.path.dirname(statick_tool.__file__),
                                          'plugins')])
    manager.setCategoriesFilter({
        "Reporting": ReportingPlugin,
    })
    manager.collectPlugins()
    # Verify that a plugin's get_name() function returns "upload_risk_assessment"
    assert any(plugin_info.plugin_object.get_name() == 'upload_risk_assessment' for
               plugin_info in manager.getPluginsOfCategory("Reporting"))
    # While we're at it, verify that a plugin is named JSON Risk Assessment Reporting Plugin
    assert any(plugin_info.name == 'JSON Risk Assessment Reporting Plugin' for
               plugin_info in manager.getPluginsOfCategory("Reporting"))


def test_json_reporting_plugin_report_valid():
    """Validate the output of the plugin."""
    jrarp = setup_json_reporting_plugin()
    package = Package('valid_package', os.path.join(
        os.path.dirname(__file__), 'valid_package'))

    issues = {'tool_a': [
        Issue('test.txt', 1, 'tool_a', 'type', 1, 'This is a test', 'MEM50-CPP')]}
    try:
        os.makedirs('valid_package-level')
    except OSError:
        # directory exists - that's fine
        # TODO: After py27 support is dropped, there's a kwarg for makedirs which suppresses this error
        pass
    jrarp.report(package, issues, 'level')
    with open(os.path.join('valid_package-level', 'valid_package-level.json')) as jsonfile:
        output = json.load(jsonfile)
        assert output['issue_count_by_tool']['tool_a'] == 1
        assert output['risk_assessment']['analysis_type'] == 'level'
        assert output['risk_assessment']['package_analyzed'] == 'valid_package'
        assert output['risk_assessment']['risks_per_level']['High'] == 1
        assert output['risk_assessment']['cert_references_per_level']['High']['MEM50-CPP'] == 1


def test_verify_config():
    """ verify the cfg data gets loaded to the plugin"""
    jrarp = setup_json_reporting_plugin()
    jrarp.load_cfg()
    assert jrarp.cfg


def test_verify_config_has_rest_info():
    """ Verify connection to rest services """
    jrarp = setup_json_reporting_plugin()
    jrarp.load_cfg()

    assert 'rom' in jrarp.cfg and 'rest' in jrarp.cfg['rosm']


def test_verify_config_has_rest_info():
    """ Verify the cfg file has rest info in it """
    jrarp = setup_json_reporting_plugin()
    jrarp.load_cfg()
    assert 'url' in jrarp.cfg['rosm']['rest'] and \
        'apiKey' in jrarp.cfg['rosm']['rest'] and \
        'packagesEndpoint' in jrarp.cfg['rosm']['rest']


def test_verify_rest_post_command():
    """ Verify REST post command with package data """
    cur_path = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(cur_path, './example_package.json')) as json_file:
        example_package_data_json = json.load(json_file)
    jrarp = setup_json_reporting_plugin()
    jrarp.load_cfg()
    st = jrarp.post_stats(example_package_data_json)
    assert st == requests.codes.ok or st == requests.codes.created


def get_packages(cfg):
    headers = {'Content-Type': 'application/json',
               'rosm-api-key': cfg['rosm']['rest']['apiKey']}

    r = requests.get(cfg['rosm']['rest']['url'] + cfg['rosm']
                     ['rest']['packagesEndpoint'], headers=headers)
    return r.json()


def get_package(cfg, package_id):
    headers = {'Content-Type': 'application/json',
               'rosm-api-key': cfg['rosm']['rest']['apiKey']}

    r = requests.get(cfg['rosm']['rest']['url'] + cfg['rosm']
                     ['rest']['packagesEndpoint']+"/"+package_id, headers=headers)
    return r.json()


def test_verify_rest_put_command():
    """ Verify REST put/update command for package statick data """

    jrarp = setup_json_reporting_plugin()
    jrarp.load_cfg()
    packages = get_packages(jrarp.cfg)

    cur_path = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(cur_path, './example_package.json')) as json_file:
        example_package_data_json = json.load(json_file)

    pkg_id = None
    for pkg in packages:
        if pkg['name'] == example_package_data_json['name'].lower():
            pkg_id = pkg['_id']

    # verify package
    assert (pkg_id is not None)

    # remove the ID so we can create a new one
    example_package_data_json['_id'] = pkg_id

    high = random.randint(1, 101)
    unknown = random.randint(1, 101)

    # example values to update the entry
    example_package_data_json['staticAnalysis']['risks'] = {
        "high": high,
        "low": 112,
        "moderate": 312,
        "unknown": unknown
    }

    now = datetime.now()  # current date and time
    static_date = now.strftime("%Y-%m-%d")
    example_package_data_json['staticAnalysis']['staticAnalysisDate'] = static_date

    if (not example_package_data_json):
        assert False

    st = jrarp.put_statick_data(example_package_data_json)
    assert st == requests.codes.ok or st == requests.codes.created

    existing_pkg = get_package(jrarp.cfg, example_package_data_json['_id'])
    # verify data fields
    assert existing_pkg['staticAnalysis']['risks']['high'] == high
    assert existing_pkg['staticAnalysis']['risks']['unknown'] == unknown
    assert existing_pkg['staticAnalysis']['staticAnalysisDate'] == static_date
