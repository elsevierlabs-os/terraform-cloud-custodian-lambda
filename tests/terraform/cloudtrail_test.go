package test

import (
	"testing"

	"github.com/gruntwork-io/terratest/modules/terraform"
	"github.com/stretchr/testify/assert"
)

func TestCloudtrailExample(t *testing.T) {

	t.Parallel()

	terraformOptions := terraform.WithDefaultRetryableErrors(t, &terraform.Options{
		TerraformDir: "../../examples/cloudtrail",
	})

	defer terraform.Destroy(t, terraformOptions)

	terraform.InitAndApply(t, terraformOptions)

	lambdaFunctionName := terraform.Output(t, terraformOptions, "lambda_function_name")
	assert.Equal(t, "custodian-dev-cloudtrail", lambdaFunctionName, "lambda_function_name name is not correct")

	modeType := terraform.Output(t, terraformOptions, "mode_type")
	assert.Equal(t, "cloudtrail", modeType, "mode_type is not correct")

	cloudwatchEventRuleName := terraform.Output(t, terraformOptions, "cloudwatch_event_rule_name")
	assert.Equal(t, "custodian-dev-cloudtrail", cloudwatchEventRuleName, "cloudwatch_event_rule_name is not correct")

	cloudwatchEventPattern := terraform.Output(t, terraformOptions, "cloudwatch_event_pattern")
	expectedCloudwatchEventPattern := `
{
	"detail": {
		"eventName": [
			"AuthorizeSecurityGroupIngress",
			"RevokeSecurityGroupIngress"
		],
		"eventSource": [
			"ec2.amazonaws.com"
		]
	},
	"detail-type": [
		"AWS API Call via CloudTrail"
	]
}`
	assert.JSONEq(t, expectedCloudwatchEventPattern, cloudwatchEventPattern, "cloudwatch_event_pattern does not match expected structure")

}
