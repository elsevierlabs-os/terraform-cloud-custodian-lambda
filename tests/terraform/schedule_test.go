package test

import (
	"testing"

	"github.com/gruntwork-io/terratest/modules/terraform"
	"github.com/stretchr/testify/assert"
)

func TestSchedulecExample(t *testing.T) {

	t.Parallel()

	terraformOptions := terraform.WithDefaultRetryableErrors(t, &terraform.Options{
		TerraformDir: "../../examples/schedule",
		Vars: map[string]interface{}{
			"create_schedule_s3_bucket": false,
		},
	})

	defer terraform.Destroy(t, terraformOptions)

	terraform.InitAndApply(t, terraformOptions)

	lambdaFunctionName := terraform.Output(t, terraformOptions, "lambda_function_name")
	assert.Equal(t, "custodian-dev-schedule", lambdaFunctionName, "lambda_function_name is not correct")

	modeType := terraform.Output(t, terraformOptions, "mode_type")
	assert.Equal(t, "schedule", modeType, "mode_type is not correct")

	eventBridgeScheduleName := terraform.Output(t, terraformOptions, "eventbridge_schedule_name")
	assert.Equal(t, "custodian-dev-schedule", eventBridgeScheduleName, "eventbridge_schedule_name is not correct")

	eventBridgeScheduleExpression := terraform.Output(t, terraformOptions, "eventbridge_schedule_expression")
	assert.Equal(t, "rate(5 minutes)", eventBridgeScheduleExpression, "eventbridge_schedule_expression is not correct")

	eventBridgeScheduleTimezone := terraform.Output(t, terraformOptions, "eventbridge_schedule_timezone")
	assert.Equal(t, "Europe/London", eventBridgeScheduleTimezone, "eventbridge_schedule_timezone is not correct")

	eventBridgeScheduleGroupName := terraform.Output(t, terraformOptions, "eventbridge_schedule_group_name")
	assert.Equal(t, "custodian-dev-schedule-group", eventBridgeScheduleGroupName, "eventbridge_schedule_group_name is not correct")
}
