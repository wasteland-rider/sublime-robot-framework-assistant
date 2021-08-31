*** Settings ***
Documentation    Relative imports paths to libraries

*** Variables ***
${suite_tree}   ${CURDIR}/../suite_tree
${real_tree}    ../real_suite
${real_resource}    ${real_tree}/resource/
${real_resource_2}    ${real_resource}/resource2
${some_resource}    ${CURDIR}${/}..