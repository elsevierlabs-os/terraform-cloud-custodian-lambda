package test

import (
	"testing"

	"github.com/gruntwork-io/terratest/modules/terraform"
	"github.com/stretchr/testify/assert"
)

func TestMailerExample(t *testing.T) {

	terraformOptions := terraform.WithDefaultRetryableErrors(t, &terraform.Options{
		TerraformDir: "../../examples/mailer",
	})

	defer terraform.Destroy(t, terraformOptions)

	terraform.InitAndApply(t, terraformOptions)

	lambdaFunctionName := terraform.Output(t, terraformOptions, "lambda_function_name")
	assert.Equal(t, "cloud-custodian-dev-mailer", lambdaFunctionName, "lambda_function_name is not correct")

	lambdaFunction := terraform.OutputMap(t, terraformOptions, "lambda_function")
	region := terraform.Output(t, terraformOptions, "region")
	assert.Equal(t, region, lambdaFunction["region"], "region from mailer config should be same region as lambda_function")

	eventRuleName := terraform.Output(t, terraformOptions, "event_rule_name")
	assert.Equal(t, "cloud-custodian-dev-mailer", eventRuleName, "event_rule_name is not correct")

	eventRuleScheduleExpression := terraform.Output(t, terraformOptions, "event_rule_schedule_expression")
	assert.Equal(t, "rate(10 minutes)", eventRuleScheduleExpression, "event_rule_schedule_expression is not correct")

	lambdaRole := terraform.Output(t, terraformOptions, "lambda_function_role")
	assert.Contains(t, lambdaRole, "arn:aws:iam::", "lambda_function_role should be resolved to a full ARN")
	assert.Contains(t, lambdaRole, "role/cloud-custodian-dev-mailer", "lambda_function_role should contain the expected role name")

	// Get hashes and package versions from first apply
	firstSha256Base64 := terraform.Output(t, terraformOptions, "lambda_function_source_code_hash")
	firstSha256Hex := terraform.Output(t, terraformOptions, "sha256_hex")
	firstPackageVersions := terraform.Output(t, terraformOptions, "package_versions")

	// Second apply to ensure idempotency with hashes and package versions
	terraform.Apply(t, terraformOptions)

	// Get hashes and package versions from second apply
	secondSha256Base64 := terraform.Output(t, terraformOptions, "lambda_function_source_code_hash")
	secondSha256Hex := terraform.Output(t, terraformOptions, "sha256_hex")
	secondPackageVersions := terraform.Output(t, terraformOptions, "package_versions")

	// Verify hashes and package versions are identical from first and second apply which proves idempotency
	assert.Equal(t, firstSha256Base64, secondSha256Base64,
		"Lambda source code hash (base64) should be identical across multiple applies when no changes are made")
	assert.Equal(t, firstSha256Hex, secondSha256Hex,
		"Lambda source code hash (hex) should be identical across multiple applies when no changes are made")
	assert.Equal(t, firstPackageVersions, secondPackageVersions,
		"Package versions should be identical across multiple applies when no changes are made")
}

func TestMailerExampleRegionChange(t *testing.T) {

	terraformOptions := terraform.WithDefaultRetryableErrors(t, &terraform.Options{
		TerraformDir: "../../examples/mailer",
	})

	terraform.InitAndApply(t, terraformOptions)

	// Second apply with region change
	terraformOptionsRegionChange := terraform.WithDefaultRetryableErrors(t, &terraform.Options{
		TerraformDir: "../../examples/mailer",

		Vars: map[string]interface{}{
			"region": "us-east-1",
		},
	})

	defer terraform.Destroy(t, terraformOptionsRegionChange)
	terraform.Apply(t, terraformOptionsRegionChange)

	lambdaFunction := terraform.OutputMap(t, terraformOptionsRegionChange, "lambda_function")
	assert.Equal(t, "us-east-1", lambdaFunction["region"], "region from mailer config should now be us-east-1")
}
