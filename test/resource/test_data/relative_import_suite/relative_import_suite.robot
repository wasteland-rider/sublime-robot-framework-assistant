*** Settings ***
Resource    ./Paths.robot
Library    ${suite_tree}/LibNoClass.py
Library    ${real_tree}/libs/SuiteLib.py
Resource    ${real_resource}/resource1/real_suite_resource.robot
Variables    ${real_resource_2}/var_file/variables.py

*** Variables ***
${some_variable}    Some variable

*** Keywords ***
Some Keyword 1

Some Keyword 2