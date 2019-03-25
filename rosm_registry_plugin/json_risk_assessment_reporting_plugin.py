"""Plugin to generate .json reports for the ROS-M registry."""
from __future__ import print_function

import json
import os
from collections import OrderedDict

from statick_tool.plugins.reporting.rosm_registry_plugin import risk_analyzer
from statick_tool.reporting_plugin import ReportingPlugin


class JSONRiskAssessmentReportingPlugin(ReportingPlugin):
    """A plugin to generate a JSON with a risk assessment."""

    def get_name(self):
        """Get the name of the reporting plugin."""
        return 'upload_risk_assessment'

    def report(self, package, issues, level):
        """
        Upload the risk assessment to a web endpoint.

        Args:
            package (:obj:`Package`): The Package object that was analyzed.
            issues (:obj:`dict` of :obj:`str` to :obj:`Issue`): The issues
                found by the Statick analysis, keyed by the tool that found
                them.
            level: (:obj:`str`): Name of the level used in the scan
        """
        risk_assessment = risk_analyzer.get_risk_analysis(issues, self.plugin_context,
                                                          package.name, level)
        output_dict = {}
        output_dict['risk_assessment'] = risk_assessment.to_dict()
        output_dict['issue_count_by_tool'] = {}
        for key, value in list(issues.items()):
            unique_issues = list(OrderedDict.fromkeys(value))
            output_dict['issue_count_by_tool'][key] = len(unique_issues)

        # Write the file
        output_dir = os.path.join(self.plugin_context.args.output_directory,
                                  package.name + "-" + level)

        output_file = os.path.join(output_dir,
                                   package.name + "-" + level + ".json")
        print("Writing output to {}".format(output_file))
        with open(output_file, "w") as out:
            out.write(json.dumps(output_dict))
