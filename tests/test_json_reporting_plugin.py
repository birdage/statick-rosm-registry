"""json reporting plugin unit tests."""
import argparse
import json
import os

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
    plugin_context = PluginContext(arg_parser.parse_args([os.getcwd()]), resources, config)
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
    package = Package('valid_package', os.path.join(os.path.dirname(__file__),
                                                    'valid_package'))

    issues = {'tool_a': [Issue('test.txt', 1, 'tool_a', 'type', 1, 'This is a test', 'MEM50-CPP')]}
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
