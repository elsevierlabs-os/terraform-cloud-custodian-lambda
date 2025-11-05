package test

import (
	"testing"

	"github.com/gruntwork-io/terratest/modules/terraform"
	"github.com/stretchr/testify/assert"
)

func TestPeriodicExample(t *testing.T) {

	t.Parallel()

	terraformOptions := terraform.WithDefaultRetryableErrors(t, &terraform.Options{
		TerraformDir: "../../examples/periodic",
	})

	defer terraform.Destroy(t, terraformOptions)

	terraform.InitAndApply(t, terraformOptions)

	lambdaFunctionName := terraform.Output(t, terraformOptions, "lambda_function_name")
	assert.Equal(t, "custodian-dev-periodic", lambdaFunctionName, "lambda_function_name is not correct")

	modeType := terraform.Output(t, terraformOptions, "mode_type")
	assert.Equal(t, "periodic", modeType, "mode_type is not correct")

	periodicEventRuleName := terraform.Output(t, terraformOptions, "periodic_event_rule_name")
	assert.Equal(t, "custodian-dev-periodic", periodicEventRuleName, "periodic_event_rule_name is not correct")

	periodicScheduleExpression := terraform.Output(t, terraformOptions, "periodic_schedule_expression")
	assert.Equal(t, "rate(5 minutes)", periodicScheduleExpression, "periodic_schedule_expression is not correct")

	lambdaRole := terraform.Output(t, terraformOptions, "lambda_function_role")
	assert.Contains(t, lambdaRole, "arn:aws:iam::", "lambda_function_role should be resolved to a full ARN")
	assert.Contains(t, lambdaRole, "role/custodian-dev-periodic", "lambda_function_role should contain the expected role name")

	lambdaFunction := terraform.OutputMap(t, terraformOptions, "lambda_function")
	assert.Equal(t, "300", lambdaFunction["timeout"], "lambda_function timeout not the same as specified in policies")
	assert.Equal(t, "256", lambdaFunction["memory_size"], "lambda_function memory not the same as specified in policies")

	lambdaTags := terraform.OutputMap(t, terraformOptions, "lambda_function_tags")
	assert.Equal(t, "true", lambdaTags["Test"], "The 'Test' tag is missing or incorrect.")
	assert.Contains(t, lambdaTags["custodian-info"], "mode=periodic", "The 'custodian-info' tag should include the mode.")
	assert.Contains(t, lambdaTags["custodian-info"], "version", "The 'custodian-info' tag should include the version.")

	// Get SHA256 hash from first apply
	firstSha256Base64 := terraform.Output(t, terraformOptions, "lambda_function_source_code_hash")
	firstSha256Hex := terraform.Output(t, terraformOptions, "sha256_hex")
	firstPackageVersions := terraform.Output(t, terraformOptions, "package_versions")

	// Second apply to ensure idempotency with the SHA256 hash
	terraform.Apply(t, terraformOptions)

	// Get SHA256 hash from second apply
	secondSha256Base64 := terraform.Output(t, terraformOptions, "lambda_function_source_code_hash")
	secondSha256Hex := terraform.Output(t, terraformOptions, "sha256_hex")
	secondPackageVersions := terraform.Output(t, terraformOptions, "package_versions")

	// Verify hashes are identical from first and second apply which proves idempotency
	assert.Equal(t, firstSha256Base64, secondSha256Base64,
		"Lambda source code hash (base64) should be identical across multiple applies when no changes are made")
	assert.Equal(t, firstSha256Hex, secondSha256Hex,
		"Lambda source code hash (hex) should be identical across multiple applies when no changes are made")
	assert.Equal(t, firstPackageVersions, secondPackageVersions,
		"Package versions should be identical across multiple applies when no changes are made")
}
