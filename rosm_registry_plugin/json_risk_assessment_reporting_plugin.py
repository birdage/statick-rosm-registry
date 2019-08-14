"""Plugin to generate .json reports for the ROS-M registry."""
from __future__ import print_function

import json
import os
import requests
import yaml
from collections import OrderedDict

from statick_tool.plugins.reporting.rosm_registry_plugin import risk_analyzer
from statick_tool.reporting_plugin import ReportingPlugin


class JSONRiskAssessmentReportingPlugin(ReportingPlugin):
    """A plugin to generate a JSON with a risk assessment."""

    def __init__(self):
        self.cfg = None

    # pyflakes: disable=no-self-use
    def get_name(self):
        """Get the name of the reporting plugin."""
        return 'upload_risk_assessment'
    # pyflakes: enable=no-self-use

    def load_cfg(self):
        """
        Load the ROSM configuration file
        """
        cfg_path = self.plugin_context.resources.get_file("config.yaml")
        try:

            with open(cfg_path, 'r') as ymlfile:
                cfg = yaml.load(ymlfile, Loader=yaml.FullLoader)
                self.cfg = (cfg)
        except IOError:
            print('error loading ROSM configuration file')

    def put_statick_data(self, package_data):
        """
        Performs an update/put request for statick data to the ROSM REST services endpoint
        """
        headers = {'Content-Type': 'application/json',
                   'rosm-api-key': self.cfg['rosm']['rest']['apiKey']}

        pkg_link = self.cfg['rosm']['rest']['url'] + \
            self.cfg['rosm']['rest']['packagesEndpoint'] + \
            '/' + package_data['_id']
        r = requests.put(pkg_link,
                         headers=headers,
                         data=json.dumps(package_data)
                         )

        if (not(r.status_code == requests.codes.created or r.status_code == requests.codes.ok)):
            raise Exception('ERROR Performing Request...')
        if ('error' in r.json()):
            print(r.json())
            raise Exception('ERROR Performing Request::', r.json()['error'])
        return r.status_code

    def post_stats(self, package_data):
        """
        Performs the post request to the ROSM REST services endpoint
        """
        headers = {'Content-Type': 'application/json',
                   'rosm-api-key': self.cfg['rosm']['rest']['apiKey']}

        r = requests.post(self.cfg['rosm']['rest']['url'] + self.cfg['rosm']['rest']['packagesEndpoint'],
                          headers=headers,
                          data=json.dumps(package_data)
                          )

        if (not(r.status_code == requests.codes.created or r.status_code == requests.codes.ok)):
            raise Exception('ERROR Performing Request...')
        if ('error' in r.json()):
            raise Exception('ERROR Performing Request::', r.json()['error'])
        return r.status_code

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
        self.load_cfg()

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
            out.write(json.dumps(output_dict, indent=2))
