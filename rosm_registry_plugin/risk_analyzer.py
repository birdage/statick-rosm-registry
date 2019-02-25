"""Calculates security risk from a list of CERT issue types."""
from __future__ import print_function

import csv
import time

_risk_analysis = None


def get_risk_analysis(issues, plugin_context, package_name, level):
    """
    Singleton interface to the RiskAnalyzer/RiskAnalysis.

    You can instantiate your own RiskAnalyzer if you really want, but the
    expected use case is that you'll just run the analysis once. This method
    generates the analyzer and performs the analysis exactly once and returns
    the same analysis every time it's called thereafter.

    Args:
        issues (:obj:`dict` of :obj:`str` to :obj:`Issue`): Map of tools to
               the issues they returned.
    """
    global _risk_analysis
    if _risk_analysis is None:
        risk_analyzer = RiskAnalyzer(package_name, level, plugin_context.resources.get_file("cert_severity_likelihood.txt"))
        _risk_analysis = risk_analyzer.generate_analysis(issues)
    return _risk_analysis


class RiskAnalyzer(object):
    """
    A plugin to convert CERT issues to risk assessments.

    Performs qualitative risk assessments using the CMU SEI's mapping
    of rule violations to the severity of the issue and the likelihood
    of the issue occurring/being exploited.

    The initial version of this plugin intentionally disregards the
    remediation cost included in the CERT priority/levels mapping, which
    is why we aren't just using the provided L1/2/3 format.
    """

    SEVERITY_LIKELIHOOD_MAP = {'Low': {'Unlikely': 'Low', 'Probable': 'Low', 'Likely': 'Low'}, 'Medium': {'Unlikely': 'Low', 'Probable': 'Moderate', 'Likely': 'Moderate'},
                               'High': {'Unlikely': 'Low', 'Probable': 'Moderate', 'Likely': 'High'}}
    rule_to_analysis = {}
    analysis = None

    def __init__(self, package_name, level, file_path):
        """
        Initialize the risk analyzer, load the rules list.

        Args:
            file_path (str): Path to the rule-to-analysis mapping file
        """
        self.analysis = RiskAnalysis(package_name, level)
        with open(file_path, 'r') as (mapping_file):
            reader = csv.DictReader(mapping_file)
            for line in reader:
                self.rule_to_analysis[line['rule']] = line

    def generate_analysis(self, issues):
        """
        Generate a risk analysis based on a list of CERT rule violations.

        Args:
            issues (:obj:`dict` of :obj:`str` to :obj:`Issue`) dict of
                rule violations
        """
        print('---Generating Risk Analysis---')
        for tool in list(issues.items()):
            self.analysis.add_tool(tool[0])
            for violation in tool[1]:
                if violation.cert_reference in self.rule_to_analysis.keys():
                    severity = self.rule_to_analysis[violation.cert_reference]['severity']
                    likelihood = self.rule_to_analysis[violation.cert_reference]['likelihood']
                    self.analysis.add_issue(self.SEVERITY_LIKELIHOOD_MAP[severity][likelihood], violation.cert_reference)
                elif violation.cert_reference is not None:
                    print("Couldn't look up rule " + violation.cert_reference)
        self.analysis.timestamp = time.time()
        return self.analysis


class RiskAnalysis(object):
    """
    A report of the security risks found in scanned code.

    This class stores the risk impacts and corresponding rules that are passed to it
    and outputs a dict containing the risk summary (suitable to send to a risk analysis
    registry).
    """

    IMPACT_TO_INT = {'High': 2, 'Moderate': 1, 'Low': 0, 'No Risks Found': -998, 'Unknown': -999}
    highest_risk_level = 'No Risks Found'
    risks_per_level = {'High': 0, 'Moderate': 0, 'Low': 0, 'Unknown': 0}
    cert_references_per_level = {'High': {}, 'Moderate': {}, 'Low': {}, 'Unknown': {}}
    tools = set()
    timestamp = 0
    package_name = ''
    level = ''

    def __init__(self, package_name, level):
        """
        Initialize a RiskAnalysis.

        Args:
            package_name (str): The name of the package that was analyzed.
            level (str): The level of the scan that was performed.
        """
        self.package_name = package_name
        self.level = level

    def add_tool(self, tool):
        """Add a tool to the tools list."""
        self.tools.add(tool)

    def add_issue(self, impact, cert_reference):
        """
        Add an impact with (optional) CERT rule reference to the risks.

        Args:
            impact (str): The impact level of a violation, expected to be in IMPACT_TO_INT
                          (or None if the impact is unknown)
            cert_reference (str, optional): The CERT rule corresponding to the violation
        """
        if impact in self.risks_per_level.keys():
            self.risks_per_level[impact] += 1
            if cert_reference is not None:
                if cert_reference in self.cert_references_per_level[impact].keys():
                    self.cert_references_per_level[impact][cert_reference] += 1
                else:
                    self.cert_references_per_level[impact][cert_reference] = 1
            if self.IMPACT_TO_INT[impact] > self.IMPACT_TO_INT[self.highest_risk_level]:
                self.highest_risk_level = impact
        else:
            self.risks_per_level['Unknown'] += 1
            if cert_reference is not None:
                if cert_reference in self.cert_references_per_level['Unknown'].keys():
                    self.cert_references_per_level['Unknown'][cert_reference] += 1
                else:
                    self.cert_references_per_level['Unknown'][cert_reference] = 1

    def to_dict(self):
        """Return a representation of the analysis as a dict."""
        result = {}
        result['package_analyzed'] = self.package_name
        result['analysis_type'] = self.level
        result['highest_risk_level'] = self.highest_risk_level
        result['risks_per_level'] = self.risks_per_level
        result['cert_references_per_level'] = self.cert_references_per_level
        result['tools_used'] = list(self.tools)
        result['timestamp'] = self.timestamp
        return result
