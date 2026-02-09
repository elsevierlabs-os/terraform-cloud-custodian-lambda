package test

import (
	"sort"
	"testing"

	"github.com/gruntwork-io/terratest/modules/terraform"
	"github.com/stretchr/testify/assert"
)

func TestMultiRegionVarsExample(t *testing.T) {

	terraformOptions := terraform.WithDefaultRetryableErrors(t, &terraform.Options{
		TerraformDir: "../../examples/multi-region",
		Vars: map[string]interface{}{
			"create_multi_region_s3_bucket": false,
		},
	})

	defer terraform.Destroy(t, terraformOptions)

	terraform.InitAndApply(t, terraformOptions)

	lambdaFunctionRegions := getSortedOutputKeys(t, terraformOptions, "lambda_function_name")

	regions := terraform.OutputList(t, terraformOptions, "regions")
	sort.Strings(regions)

	assert.Equal(t, lambdaFunctionRegions, regions, "lambda function should be deployed to all regions")
}

func TestMultiRegionPolicyExample(t *testing.T) {

	// First apply with targets
	target := "module.cloud_custodian_lambda.data.external.package_lambda"

	terraformOptionsTarget := terraform.WithDefaultRetryableErrors(t, &terraform.Options{
		TerraformDir: "../../examples/multi-region",

		Targets: []string{target},

		Vars: map[string]interface{}{
			"regions":                      []string{},
			"create_multi_region_s3_bucket": false,
		},
	})

	terraform.InitAndApply(t, terraformOptionsTarget)

	// Second apply without targets
	terraformOptions := terraform.WithDefaultRetryableErrors(t, &terraform.Options{
		Vars: map[string]interface{}{
			"regions":                      []string{},
			"create_multi_region_s3_bucket": false,
		},
		TerraformDir: "../../examples/multi-region",
	})

	defer terraform.Destroy(t, terraformOptions)
	terraform.Apply(t, terraformOptions)

	lambdaFunctionRegions := getSortedOutputKeys(t, terraformOptions, "lambda_function_name")

	regions := terraform.OutputList(t, terraformOptions, "regions")
	sort.Strings(regions)

	assert.Equal(t, lambdaFunctionRegions, regions, "lambda function should be deployed to all regions")
}
