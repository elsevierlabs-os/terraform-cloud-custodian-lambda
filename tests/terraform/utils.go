package test

import (
	"sort"
	"testing"

	"github.com/gruntwork-io/terratest/modules/terraform"
)

// getSortedOutputKeys extracts and sorts the keys from a Terraform output map.
// This is useful for comparing output maps against expected lists in a consistent order.
func getSortedOutputKeys(t *testing.T, options *terraform.Options, outputName string) []string {
	// OutputMap is guaranteed to return a non-nil map, or panic if the output is missing.
	outputMap := terraform.OutputMap(t, options, outputName)

	keys := make([]string, 0, len(outputMap))
	for k := range outputMap {
		keys = append(keys, k)
	}
	sort.Strings(keys)
	return keys
}

// getOutputMapOfStringLists extracts a map of string lists from a Terraform output.
// This is useful for outputs where each key maps to a list of strings.
func getOutputMapOfStringLists(t *testing.T, options *terraform.Options, outputName string) map[string][]string {
	// Get all outputs and navigate to the specific output
	allOutputs := terraform.OutputAll(t, options)
	outputValue := allOutputs[outputName].(map[string]interface{})

	result := make(map[string][]string)
	for key, value := range outputValue {
		// Convert []interface{} to []string
		listInterface := value.([]interface{})
		listStrings := make([]string, len(listInterface))
		for i, v := range listInterface {
			listStrings[i] = v.(string)
		}
		result[key] = listStrings
	}
	return result
}
