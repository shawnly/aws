# AWS Tags Parser Module

This module parses an AWS resource tag value into separate variables.

## Inputs

* `tag_key`: The key of the AWS resource tag (default: "DomainEC2Map")
* `tag_value`: The value of the AWS resource tag (default: "xsv-dev-01")

## Outputs

* `project`: The project part of the tag value
* `env`: The environment part of the tag value
* `number`: The number part of the tag value