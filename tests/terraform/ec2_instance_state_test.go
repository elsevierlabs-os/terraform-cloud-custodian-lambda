package test

import (
	"testing"

	"github.com/gruntwork-io/terratest/modules/terraform"
	"github.com/stretchr/testify/assert"
)

func TestEc2InstanceStateExample(t *testing.T) {

	t.Parallel()

	terraformOptions := terraform.WithDefaultRetryableErrors(t, &terraform.Options{
		TerraformDir: "../../examples/ec2-instance-state",
		Vars: map[string]interface{}{
			"create_ec2_instance_state_s3_bucket": false,
		},
	})

	defer terraform.Destroy(t, terraformOptions)

	terraform.InitAndApply(t, terraformOptions)

	lambdaFunctionName := terraform.Output(t, terraformOptions, "lambda_function_name")
	assert.Equal(t, "custodian-dev-ec2-instance-state", lambdaFunctionName, "lambda_function_name is not correct")

	modeType := terraform.Output(t, terraformOptions, "mode_type")
	assert.Equal(t, "ec2-instance-state", modeType, "mode_type is not correct")

	cloudwatchEventRuleName := terraform.Output(t, terraformOptions, "cloudwatch_event_rule_name")
	assert.Equal(t, "custodian-dev-ec2-instance-state", cloudwatchEventRuleName, "cloudwatch_event_rule_name is not correct")

	cloudwatchEventPattern := terraform.Output(t, terraformOptions, "cloudwatch_event_pattern")
	expectedCloudwatchEventPattern := `
{
	"detail": {
		"state": [
			"terminated"
		]
	},
	"detail-type": [
		"EC2 Instance State-change Notification"
	],
	"source": [
		"aws.ec2"
	]
}`
	assert.JSONEq(t, expectedCloudwatchEventPattern, cloudwatchEventPattern, "cloudwatch_event_pattern does not match expected structure")

	// Get SHA256 hash from first apply
	nonForceDeploySha256Base64 := terraform.Output(t, terraformOptions, "lambda_function_source_code_hash")

	// Second apply with force_deploy set to true to ensure this changes lambda to a new hash
	terraformOptionsForceDeploy := terraform.WithDefaultRetryableErrors(t, &terraform.Options{
		TerraformDir: "../../examples/ec2-instance-state",

		Vars: map[string]interface{}{
			"force_deploy":                      true,
			"create_ec2_instance_state_s3_bucket": false,
		},
	})

	defer terraform.Destroy(t, terraformOptionsForceDeploy)

	terraform.InitAndApply(t, terraformOptionsForceDeploy)

	forceDeploySha256Base64 := terraform.Output(t, terraformOptions, "lambda_function_source_code_hash")

	assert.NotEqual(t, nonForceDeploySha256Base64, forceDeploySha256Base64,
		"Lambda source code hash (base64) should change when force_deploy is true")
}
